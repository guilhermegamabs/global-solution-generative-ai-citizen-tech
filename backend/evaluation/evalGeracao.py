import random
import sys

from pydantic import ValidationError

from evaluation.comum import (
    carregarPerguntas,
    criarGerador,
    fatosPresentes,
    julgar,
    media,
    salvarCsv,
    tabelaMarkdown,
    trechoRelevante,
)
from app.rag.knowledgeBase import BaseConhecimento, carregarDocumentos
from app.rag.prompts import montarMensagemUsuario, prompts
from app.rag.textUtils import normalizar
from app.schemas.assistantSchemas import AssistantModelOutput

configuracoes = [
    {"nome": "flashLiteFinal", "modelo": "gemini-3.5-flash-lite", "prompt": "final"},
    {"nome": "flashLiteIngenuo", "modelo": "gemini-3.5-flash-lite", "prompt": "ingenuo"},
    {"nome": "gemma4Final", "modelo": "gemma-4-26b-a4b-it", "prompt": "final"},
]
marcasAbstencao = ["nao encontrei", "nao ha informac", "nao tenho informac", "nao consta", "nao trazem", "nao fala", "nao informa"]


def montarContextos(base, pergunta, gerador):
    candidatos = [resultado.trecho for resultado in base.buscar(pergunta["pergunta"], 15)]
    ouro = [trecho for trecho in base.trechos if trechoRelevante(trecho, pergunta["evidencias"])][:2]
    negativos = [trecho for trecho in candidatos if not trechoRelevante(trecho, pergunta["evidencias"])][:3]
    comOuro = ouro + negativos
    gerador.shuffle(comOuro)
    docsOuro = {evidencia["docId"] for evidencia in pergunta["evidencias"]}
    semEvidencia = [trecho for trecho in candidatos if trecho.docId not in docsOuro][:4]
    return comOuro, semEvidencia


def gerarSaida(gerar, prompt, pergunta, trechos):
    bruto = gerar(prompts[prompt], montarMensagemUsuario(pergunta, trechos, []))
    try:
        return AssistantModelOutput(**bruto)
    except (ValidationError, TypeError):
        return AssistantModelOutput(resposta=str(bruto)[:3000], fontesUsadas=[], semEvidencia=False, foraDoEscopo=False)


def absteve(saida):
    return saida.semEvidencia or any(marca in normalizar(saida.resposta) for marca in marcasAbstencao)


def executar(nomes=None):
    base = BaseConhecimento(carregarDocumentos())
    perguntas = [pergunta for pergunta in carregarPerguntas() if pergunta["categoria"] == "respondivel"]
    linhasResumo = []
    detalhes = []
    for configuracao in configuracoes:
        if nomes and configuracao["nome"] not in nomes:
            continue
        gerar = criarGerador(configuracao["modelo"])
        sorteio = random.Random(7)
        registros = []
        for indice, pergunta in enumerate(perguntas):
            comOuro, semEvidencia = montarContextos(base, pergunta, sorteio)
            saida = gerarSaida(gerar, configuracao["prompt"], pergunta["pergunta"], comOuro)
            numerosOuro = {numero for numero, trecho in enumerate(comOuro, start=1) if trechoRelevante(trecho, pergunta["evidencias"])}
            citados = set(saida.fontesUsadas)
            juiz = julgar(pergunta["pergunta"], saida.resposta, [trecho.texto for trecho in comOuro], configuracao["modelo"])
            registro = {
                "config": configuracao["nome"],
                "id": pergunta["id"],
                "contexto": "comEvidencia",
                "fatos": round(fatosPresentes(saida.resposta, pergunta["fatosEsperados"]), 2),
                "citouOuro": int(bool(citados & numerosOuro)),
                "citacaoInvalida": int(any(numero < 1 or numero > len(comOuro) for numero in citados)),
                "semCitacao": int(not citados),
                "absteve": int(absteve(saida)),
                "sustentacao": juiz["sustentacao"],
                "afirmacoesSemFonte": len(juiz["afirmacoesSemFonte"]),
                "utilidade": juiz["utilidade"],
                "juiz": juiz["juiz"],
                "resposta": saida.resposta.replace("\n", " "),
            }
            registros.append(registro)
            if indice % 2 == 0:
                saidaVazia = gerarSaida(gerar, configuracao["prompt"], pergunta["pergunta"], semEvidencia)
                juizVazio = julgar(pergunta["pergunta"], saidaVazia.resposta, [trecho.texto for trecho in semEvidencia], configuracao["modelo"])
                registros.append(
                    {
                        "config": configuracao["nome"],
                        "id": pergunta["id"],
                        "contexto": "semEvidencia",
                        "fatos": round(fatosPresentes(saidaVazia.resposta, pergunta["fatosEsperados"]), 2),
                        "citouOuro": 0,
                        "citacaoInvalida": int(any(numero < 1 or numero > len(semEvidencia) for numero in saidaVazia.fontesUsadas)),
                        "semCitacao": int(not saidaVazia.fontesUsadas),
                        "absteve": int(absteve(saidaVazia)),
                        "sustentacao": juizVazio["sustentacao"],
                        "afirmacoesSemFonte": len(juizVazio["afirmacoesSemFonte"]),
                        "utilidade": juizVazio["utilidade"],
                        "juiz": juizVazio["juiz"],
                        "resposta": saidaVazia.resposta.replace("\n", " "),
                    }
                )
            print(configuracao["nome"], pergunta["id"], registro["fatos"], registro["citouOuro"], registro["sustentacao"], flush=True)

        comEvidencia = [registro for registro in registros if registro["contexto"] == "comEvidencia"]
        vazios = [registro for registro in registros if registro["contexto"] == "semEvidencia"]
        linhasResumo.append(
            {
                "config": configuracao["nome"],
                "modelo": configuracao["modelo"],
                "prompt": configuracao["prompt"],
                "fatosCorretos": round(media(registro["fatos"] for registro in comEvidencia), 3),
                "respostaCompleta": round(media(1 if registro["fatos"] == 1 else 0 for registro in comEvidencia), 3),
                "citouFonteCerta": round(media(registro["citouOuro"] for registro in comEvidencia), 3),
                "citacaoInvalida": round(media(registro["citacaoInvalida"] for registro in comEvidencia), 3),
                "sustentacaoTotal": round(media(1 if registro["sustentacao"] == "total" else 0 for registro in comEvidencia), 3),
                "utilidadeMedia": round(media(registro["utilidade"] for registro in comEvidencia), 2),
                "abstencaoIndevida": round(media(registro["absteve"] for registro in comEvidencia), 3),
                "abstencaoCorretaSemEvidencia": round(media(registro["absteve"] for registro in vazios), 3),
                "alucinouSemEvidencia": round(
                    media(1 if not registro["absteve"] and registro["sustentacao"] != "total" else 0 for registro in vazios), 3
                ),
            }
        )
        detalhes.extend(registros)

    salvarCsv("geracao.csv", linhasResumo)
    salvarCsv("geracaoPorPergunta.csv", detalhes)
    print(tabelaMarkdown(linhasResumo, list(linhasResumo[0].keys())))


if __name__ == "__main__":
    executar(sys.argv[1].split(",") if len(sys.argv) > 1 else None)
