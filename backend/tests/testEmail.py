import logging

import httpx
import pytest

from app.errors import EmailUnavailableError
from app.providers import emailProvider

chaveFalsa = "chave-secreta-de-teste"


class RespostaFalsa:
    def __init__(self, status, corpo):
        self.status_code = status
        self.corpo = corpo

    def json(self):
        return self.corpo


@pytest.fixture
def ambienteEmail(monkeypatch):
    monkeypatch.setenv("BREVOAPIKEY", chaveFalsa)
    monkeypatch.setenv("SENDEREMAIL", "remetente@exemplo.com")
    monkeypatch.setenv("MOSTRARCODIGONOLOG", "false")


def testeEnviaComChaveERemetenteConfigurados(ambienteEmail, monkeypatch):
    enviados = []

    def postFalso(url, json, headers, timeout):
        enviados.append((url, json, headers))
        return RespostaFalsa(201, {})

    monkeypatch.setattr(httpx, "post", postFalso)
    emailProvider.enviarCodigoPorEmail("ana@exemplo.com", "123456")
    url, corpo, cabecalhos = enviados[0]
    assert url == emailProvider.urlBrevo
    assert corpo["sender"]["email"] == "remetente@exemplo.com"
    assert corpo["to"] == [{"email": "ana@exemplo.com"}]
    assert "123456" in corpo["htmlContent"]
    assert cabecalhos["api-key"] == chaveFalsa


def testeRecusaDaBrevoViraErroAmigavelEFicaNoLogSemVazarAChave(ambienteEmail, monkeypatch, caplog):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, headers, timeout: RespostaFalsa(401, {"code": "unauthorized", "message": "Key not found"}),
    )
    with caplog.at_level(logging.ERROR, logger="orienta.email"):
        with pytest.raises(EmailUnavailableError):
            emailProvider.enviarCodigoPorEmail("ana@exemplo.com", "123456")
    assert "401" in caplog.text
    assert "Key not found" in caplog.text
    assert chaveFalsa not in caplog.text


def testeFalhaDeRedeViraErroAmigavel(ambienteEmail, monkeypatch):
    def postQuebrado(url, json, headers, timeout):
        raise httpx.ConnectError("sem rede")

    monkeypatch.setattr(httpx, "post", postQuebrado)
    with pytest.raises(EmailUnavailableError):
        emailProvider.enviarCodigoPorEmail("ana@exemplo.com", "123456")


def testeSemConfiguracaoViraErroAmigavel(monkeypatch):
    monkeypatch.setenv("BREVOAPIKEY", "")
    monkeypatch.setenv("SENDEREMAIL", "")
    monkeypatch.setenv("MOSTRARCODIGONOLOG", "false")
    with pytest.raises(EmailUnavailableError):
        emailProvider.enviarCodigoPorEmail("ana@exemplo.com", "123456")


def testeModoDeDesenvolvimentoMostraOCodigoNoTerminal(monkeypatch, capsys):
    monkeypatch.setenv("MOSTRARCODIGONOLOG", "true")
    emailProvider.enviarCodigoPorEmail("ana@exemplo.com", "654321")
    assert "654321" in capsys.readouterr().out
