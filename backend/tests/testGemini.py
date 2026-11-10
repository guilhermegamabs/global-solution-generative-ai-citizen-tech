import httpx
import pytest

from app.errors import ProviderUnavailableError
from app.providers import geminiProvider


class RespostaFalsa:
    def __init__(self, status, corpo=None):
        self.status_code = status
        self.corpo = corpo or {}

    def json(self):
        return self.corpo


respostaBoa = {"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]}


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv("GEMINIAPIKEY", "chave-de-teste")
    monkeypatch.setattr(geminiProvider.time, "sleep", lambda segundos: None)


def testeTentaDeNovoQuandoGeminiEstaSobrecarregado(ambiente, monkeypatch):
    respostas = [RespostaFalsa(503), RespostaFalsa(429), RespostaFalsa(200, respostaBoa)]
    chamadas = []

    def postFalso(url, json, headers, timeout):
        chamadas.append(1)
        return respostas[len(chamadas) - 1]

    monkeypatch.setattr(httpx, "post", postFalso)
    assert geminiProvider.gerarEstruturado("sistema", "usuario") == {"ok": True}
    assert len(chamadas) == 3


def testeDesisteDepoisDeTresFalhasTransitorias(ambiente, monkeypatch):
    chamadas = []

    def postFalso(url, json, headers, timeout):
        chamadas.append(1)
        return RespostaFalsa(503)

    monkeypatch.setattr(httpx, "post", postFalso)
    with pytest.raises(ProviderUnavailableError):
        geminiProvider.gerarEstruturado("sistema", "usuario")
    assert len(chamadas) == 3


def testeNaoRepeteErroDeChaveInvalida(ambiente, monkeypatch):
    chamadas = []

    def postFalso(url, json, headers, timeout):
        chamadas.append(1)
        return RespostaFalsa(403)

    monkeypatch.setattr(httpx, "post", postFalso)
    with pytest.raises(ProviderUnavailableError):
        geminiProvider.gerarEstruturado("sistema", "usuario")
    assert len(chamadas) == 1
