import sys
import time

from evaluation.comum import carregarPerguntas, media, salvarCsv, tabelaMarkdown, trechoRelevante
from app.rag.chunking import ConfiguracaoChunking
from app.rag.knowledgeBase import BaseConhecimento, carregarDocumentos

configuracoesChunking = [
    ConfiguracaoChunking("tamanhoFixo", 400, 0),
    ConfiguracaoChunking("tamanhoFixo", 800, 0),
    ConfiguracaoChunking("tamanhoFixo", 800, 200),
    ConfiguracaoChunking("estrutural", 400, 100),
    ConfiguracaoChunking("estrutural", 800, 200),
    ConfiguracaoChunking("estrutural", 1200, 200),
]
buscadores = ["bm25", "denso", "hibrido", "densoRerank", "hibridoRerank"]
profundidade = 10
limiares = [0.02, 0.05, 0.08, 0.1, 0.12, 0.15, 0.2, 0.3, 0.5]


def avaliarBuscador(base, perguntas):
    porPergunta = []
    inicio = time.perf_counter()
    for pergunta in perguntas:
        resultados = base.buscar(pergunta["pergunta"], profundidade)
        posicao = next(
            (indice + 1 for indice, resultado in enumerate(resultados) if trechoRelevante(resultado.trecho, pergunta["evidencias"])),
            None,
        )
        porPergunta.append(
            {
                "id": pergunta["id"],
                "posicao": posicao,
                "topo": resultados[0].trecho.chunkId if resultados else "",
                "pontuacaoTopo": round(resultados[0].pontuacao, 4) if resultados else 0,
                "caracteresTop5": sum(len(resultado.trecho.texto) for resultado in resultados[:5]),
            }
        )
    tempoMedio = (time.perf_counter() - inicio) / len(perguntas) * 1000
    return porPergunta, tempoMedio


def resumir(porPergunta):
    def acertou(item, k):
        return 1 if item["posicao"] and item["posicao"] <= k else 0

    return {
        "hit@1": round(media(acertou(item, 1) for item in porPergunta), 3),
        "hit@3": round(media(acertou(item, 3) for item in porPergunta), 3),
        "hit@5": round(media(acertou(item, 5) for item in porPergunta), 3),
        "mrr@10": round(media(1 / item["posicao"] if item["posicao"] else 0 for item in porPergunta), 3),
        "caracteresContexto": int(media(item["caracteresTop5"] for item in porPergunta)),
    }


def calibrarLimiar(documentos):
    base = BaseConhecimento(documentos)
    pontuacoes = []
    for pergunta in carregarPerguntas():
        if pergunta["categoria"] in ("adversarial", "ambigua") and not pergunta["evidencias"]:
            continue
        resultados = base.buscar(pergunta["pergunta"], 1)
        pontuacoes.append(
            {
                "id": pergunta["id"],
                "deveResponder": pergunta["esperado"] == "responder",
                "pontuacao": resultados[0].pontuacao if resultados else 0.0,
            }
        )
    linhas = []
    for limiar in limiares:
        respondiveis = [item for item in pontuacoes if item["deveResponder"]]
        semBase = [item for item in pontuacoes if not item["deveResponder"]]
        linhas.append(
            {
                "limiar": limiar,
                "respondiveisQuePassam": round(media(1 if item["pontuacao"] >= limiar else 0 for item in respondiveis), 3),
                "semBaseBarradas": round(media(1 if item["pontuacao"] < limiar else 0 for item in semBase), 3),
            }
        )
    salvarCsv("limiarRecuperacao.csv", linhas)
    salvarCsv(
        "pontuacaoTopo.csv",
        [{**item, "pontuacao": round(item["pontuacao"], 4)} for item in sorted(pontuacoes, key=lambda item: item["pontuacao"])],
    )
    print(tabelaMarkdown(linhas, list(linhas[0].keys())))


def executar():
    documentos = carregarDocumentos()
    perguntas = [pergunta for pergunta in carregarPerguntas() if pergunta["evidencias"] and pergunta["esperado"] == "responder"]
    linhas = []
    detalhes = []
    for configuracao in configuracoesChunking:
        base = BaseConhecimento(documentos, configuracao, "bm25")
        tamanhos = [len(trecho.texto) for trecho in base.trechos]
        for nome in buscadores:
            base.trocarBuscador(nome)
            porPergunta, tempoMedio = avaliarBuscador(base, perguntas)
            linha = {
                "chunking": configuracao.chave,
                "buscador": nome,
                "trechos": len(base.trechos),
                "tamanhoMedio": int(media(tamanhos)),
                **resumir(porPergunta),
                "msPorConsulta": int(tempoMedio),
            }
            linhas.append(linha)
            print(linha)
            for item in porPergunta:
                detalhes.append({"chunking": configuracao.chave, "buscador": nome, **item})

    salvarCsv("recuperacao.csv", linhas)
    salvarCsv("recuperacaoPorPergunta.csv", detalhes)
    print(tabelaMarkdown(linhas, list(linhas[0].keys())))
    calibrarLimiar(documentos)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "limiar":
        calibrarLimiar(carregarDocumentos())
    else:
        executar()
