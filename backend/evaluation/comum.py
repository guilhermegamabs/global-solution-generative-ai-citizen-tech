import csv
import hashlib
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from app.errors import InvalidModelResponseError, ProviderTimeoutError, ProviderUnavailableError
from app.providers.geminiProvider import gerarJson
from app.rag.prompts import esquemaResposta
from app.rag.textUtils import normalizar

pastaAvaliacao = Path(__file__).resolve().parent
pastaResultados = pastaAvaliacao / "resultados"
pastaCache = pastaAvaliacao / "cache"

load_dotenv(pastaAvaliacao.parent.parent / ".env")

intervaloMinimo = 4.0
ultimaChamada = [0.0]


def carregarPerguntas():
    return json.loads((pastaAvaliacao / "perguntas.json").read_text(encoding="utf-8"))


def carregarConversas():
    return json.loads((pastaAvaliacao / "conversas.json").read_text(encoding="utf-8"))


modeloJuizAlternativo = "gemini-3.5-flash-lite"


def obterModeloJuiz(modeloGerador=None):
    juiz = os.getenv("JUIZMODEL", "gemma-4-26b-a4b-it")
    if modeloGerador and modeloGerador.split("-")[0] == juiz.split("-")[0]:
        return modeloJuizAlternativo if juiz.startswith("gemma") else "gemma-4-26b-a4b-it"
    return juiz


def chamarComCache(promptSistema, mensagem, esquema, modelo, temperatura=0.2, tentativas=4):
    chave = hashlib.sha256(
        json.dumps([promptSistema, mensagem, esquema, modelo, temperatura], ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:24]
    arquivo = pastaCache / f"{chave}.json"
    if arquivo.exists():
        return json.loads(arquivo.read_text(encoding="utf-8"))
    for tentativa in range(tentativas):
        ultima = tentativa == tentativas - 1
        espera = intervaloMinimo - (time.time() - ultimaChamada[0])
        if espera > 0:
            time.sleep(espera)
        ultimaChamada[0] = time.time()
        try:
            resultado = gerarJson(promptSistema, mensagem, esquema, modelo=modelo, temperatura=temperatura)
            break
        except (ProviderUnavailableError, ProviderTimeoutError):
            if ultima:
                raise
            time.sleep(30 * (tentativa + 1))
        except InvalidModelResponseError:
            if ultima:
                raise
    pastaCache.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    return resultado


def criarGerador(modelo, registro=None):
    def gerar(promptSistema, mensagem):
        if registro is not None:
            registro.append(mensagem)
        return chamarComCache(promptSistema, mensagem, esquemaResposta, modelo)

    return gerar


def trechoRelevante(trecho, evidencias):
    texto = normalizar(trecho.texto)
    return any(trecho.docId == evidencia["docId"] and normalizar(evidencia["trecho"]) in texto for evidencia in evidencias)


def fatosPresentes(resposta, gruposFatos):
    alvo = normalizar(resposta)
    if not gruposFatos:
        return 1.0
    acertos = sum(1 for grupo in gruposFatos if any(normalizar(opcao) in alvo for opcao in grupo))
    return acertos / len(gruposFatos)


esquemaJuiz = {
    "type": "OBJECT",
    "properties": {
        "sustentacao": {"type": "STRING", "enum": ["total", "parcial", "nenhuma"]},
        "afirmacoesSemFonte": {"type": "ARRAY", "items": {"type": "STRING"}},
        "utilidade": {"type": "INTEGER"},
        "justificativa": {"type": "STRING"},
    },
    "required": ["sustentacao", "afirmacoesSemFonte", "utilidade", "justificativa"],
}

promptJuiz = (
    "Você avalia respostas de um assistente de saúde baseado em fontes. Receberá FONTES, PERGUNTA e RESPOSTA. "
    "Liste em afirmacoesSemFonte cada afirmação factual da RESPOSTA que não está apoiada nas FONTES "
    "(frases de encaminhamento genéricas como 'procure a UBS' ou 'ligue 192' só contam se contradizem as fontes). "
    "sustentacao: total se todas as afirmações factuais estão nas fontes, parcial se alguma não está, nenhuma se a maioria não está. "
    "utilidade: nota de 1 a 5 para quanto a resposta ajuda um cidadão leigo com essa pergunta (5 = resolve a dúvida com clareza). "
    "Seja rigoroso e responda em português."
)


def julgar(pergunta, resposta, contextos, modeloGerador=None):
    fontes = "\n\n".join(f"[{numero}] {texto}" for numero, texto in enumerate(contextos, start=1)) or "(nenhuma fonte)"
    mensagem = f"FONTES:\n{fontes}\n\nPERGUNTA:\n{pergunta}\n\nRESPOSTA:\n{resposta}"
    principal = obterModeloJuiz(modeloGerador)
    try:
        resultado = chamarComCache(promptJuiz, mensagem, esquemaJuiz, principal, temperatura=0.0, tentativas=2)
        return {**resultado, "juiz": principal}
    except (ProviderUnavailableError, ProviderTimeoutError, InvalidModelResponseError):
        reserva = modeloJuizAlternativo if principal != modeloJuizAlternativo else "gemma-4-26b-a4b-it"
        resultado = chamarComCache(promptJuiz, mensagem, esquemaJuiz, reserva, temperatura=0.0)
        return {**resultado, "juiz": reserva}


def salvarCsv(nome, linhas):
    pastaResultados.mkdir(parents=True, exist_ok=True)
    caminho = pastaResultados / nome
    if not linhas:
        caminho.write_text("", encoding="utf-8")
        return caminho
    campos = list(linhas[0].keys())
    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    return caminho


def salvarJson(nome, dados):
    pastaResultados.mkdir(parents=True, exist_ok=True)
    caminho = pastaResultados / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return caminho


def tabelaMarkdown(linhas, colunas):
    cabecalho = "| " + " | ".join(colunas) + " |"
    separador = "|" + "|".join("---" for _ in colunas) + "|"
    corpo = ["| " + " | ".join(str(linha.get(coluna, "")) for coluna in colunas) + " |" for linha in linhas]
    return "\n".join([cabecalho, separador, *corpo])


def media(valores):
    valores = list(valores)
    return sum(valores) / len(valores) if valores else 0.0
