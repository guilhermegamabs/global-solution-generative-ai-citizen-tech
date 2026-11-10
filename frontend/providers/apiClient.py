import os

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

chavesObrigatoriasTriagem = (
    "recordId",
    "protocol",
    "createdAt",
    "urgencyLevel",
    "recommendedService",
    "summary",
    "guidance",
    "warningSignsToWatch",
    "rationale",
    "ageRange",
    "disclaimer",
)

mensagemRespostaInvalida = "Recebemos uma resposta que não conseguimos entender. Tente novamente."


class ApiError(Exception):
    codigo = None


class SessaoExpiradaError(ApiError):
    pass


def obterUrlApi():
    return os.getenv("APIURL", "http://localhost:8000")


def obterTempoLimite():
    return float(os.getenv("APITIMEOUT", "120"))


@st.cache_resource
def obterCliente():
    return httpx.Client(base_url=obterUrlApi(), timeout=obterTempoLimite())


def lerResposta(resposta):
    try:
        corpo = resposta.json()
    except ValueError:
        raise ApiError(mensagemRespostaInvalida) from None

    if resposta.status_code >= 400:
        dados = corpo if isinstance(corpo, dict) else {}
        classe = SessaoExpiradaError if dados.get("code") == "sessionExpired" else ApiError
        erro = classe(dados.get("message") or "Algo deu errado. Tente novamente.")
        erro.codigo = dados.get("code")
        raise erro

    return corpo


def enviarRequisicao(metodo, caminho, carga=None, token=None):
    cabecalhos = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resposta = obterCliente().request(metodo, caminho, json=carga, headers=cabecalhos)
    except httpx.TimeoutException:
        raise ApiError("A análise demorou mais do que o esperado. Tente novamente em instantes.") from None
    except httpx.HTTPError:
        raise ApiError("Não conseguimos falar com o serviço agora. Tente novamente em alguns minutos.") from None

    return lerResposta(resposta)


def exigirCampos(corpo, campos):
    if not isinstance(corpo, dict) or any(campo not in corpo for campo in campos):
        raise ApiError(mensagemRespostaInvalida)
    return corpo


@st.cache_data(ttl=3600, show_spinner=False)
def buscarOpcoes():
    return exigirCampos(enviarRequisicao("GET", "/meta/options"), ("ageRanges",))


def cadastrarConta(email, senha):
    enviarRequisicao("POST", "/auth/register", {"email": email, "password": senha})


def reenviarCodigo(email):
    enviarRequisicao("POST", "/auth/resend", {"email": email})


def verificarCodigo(email, codigo):
    return exigirCampos(enviarRequisicao("POST", "/auth/verify", {"email": email, "code": codigo}), ("token", "email"))


def entrarNaConta(email, senha):
    return exigirCampos(enviarRequisicao("POST", "/auth/login", {"email": email, "password": senha}), ("token", "email"))


def sairDaConta(token):
    enviarRequisicao("POST", "/auth/logout", token=token)


def apagarConta(token):
    enviarRequisicao("DELETE", "/auth/account", token=token)


def buscarHistorico(token):
    return exigirCampos(enviarRequisicao("GET", "/history", token=token), ("records",))["records"]


def solicitarTriagem(carga, token):
    return exigirCampos(enviarRequisicao("POST", "/triage", carga, token), chavesObrigatoriasTriagem)


@st.cache_data(ttl=600, show_spinner=False)
def buscarUpasProximas(cep, limite):
    return exigirCampos(
        enviarRequisicao("POST", "/units/nearby", {"cep": cep, "limit": limite}), ("units", "origin")
    )


@st.cache_data(ttl=3600, show_spinner=False)
def buscarTemasAssistente():
    return exigirCampos(enviarRequisicao("GET", "/assistant/topics"), ("topics",))["topics"]


def perguntarAssistente(carga, token):
    return exigirCampos(
        enviarRequisicao("POST", "/assistant/ask", carga, token),
        ("answer", "status", "confidence", "sources", "alerts", "diagnostics"),
    )


def enviarRevisao(carga, token):
    return exigirCampos(enviarRequisicao("POST", "/reviews", carga, token), ("finalUrgency",))
