import os

os.environ["DATABASEURL"] = "sqlite://"
os.environ["AQUECERRAG"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.dependencies import obterEnviadorEmail, obterFontesLocalizacao, obterGerador
from app.main import aplicacao
from app.pipelines import authPipeline
from app.providers.databaseProvider import reiniciarBanco

saidaValida = {
    "urgencyLevel": "medium",
    "recommendedService": "basicUnit",
    "summary": "Sintomas de gripe sem sinais de gravidade.",
    "guidance": ["Beba bastante água.", "Descanse."],
    "warningSignsToWatch": ["Falta de ar", "Febre acima de 39 °C"],
    "rationale": "Quadro comum, sem sinais de alerta.",
}

requisicaoValida = {
    "symptoms": "Estou com dor de garganta e febre baixa desde ontem.",
    "ageRange": "adult",
    "duration": "oneToThreeDays",
    "warningSigns": [],
    "hasChronicCondition": False,
}

senhaPadrao = "senhaSegura1"
codigosEnviados = []


def enviadorFalso(destino, codigo):
    codigosEnviados.append((destino, codigo))


def ultimoCodigo(email):
    return [codigo for destino, codigo in codigosEnviados if destino == email][-1]


def sobrescreverGerador(gerar):
    aplicacao.dependency_overrides[obterGerador] = lambda: gerar


def sobrescreverFontes(fontes):
    aplicacao.dependency_overrides[obterFontesLocalizacao] = lambda: fontes


def sobrescreverEnviadorEmail(enviar):
    aplicacao.dependency_overrides[obterEnviadorEmail] = lambda: enviar


def cadastrarEVerificar(cliente, email="ana@exemplo.com", senha=senhaPadrao):
    cliente.post("/auth/register", json={"email": email, "password": senha})
    resposta = cliente.post("/auth/verify", json={"email": email, "code": ultimoCodigo(email)})
    return resposta.json()["token"]


def autenticar(cliente, token):
    cliente.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture
def clienteAnonimo():
    reiniciarBanco()
    codigosEnviados.clear()
    authPipeline.falhasLogin.clear()
    sobrescreverEnviadorEmail(enviadorFalso)
    sobrescreverGerador(lambda promptSistema, promptUsuario: dict(saidaValida))
    yield TestClient(aplicacao)
    aplicacao.dependency_overrides.clear()


@pytest.fixture
def cliente(clienteAnonimo):
    autenticar(clienteAnonimo, cadastrarEVerificar(clienteAnonimo))
    return clienteAnonimo
