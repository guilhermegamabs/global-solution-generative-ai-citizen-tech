from app.errors import ProviderTimeoutError, ProviderUnavailableError
from conftest import requisicaoValida, sobrescreverGerador


def levantarTempoEsgotado(promptSistema, promptUsuario):
    raise ProviderTimeoutError()


def levantarIndisponivel(promptSistema, promptUsuario):
    raise ProviderUnavailableError()


def testeSaude(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}


def testeOpcoes(cliente):
    corpo = cliente.get("/meta/options").json()
    assert len(corpo["ageRanges"]) == 4
    assert len(corpo["warningSigns"]) == 7


def testeTriagemComSucesso(cliente):
    resposta = cliente.post("/triage", json=requisicaoValida)
    assert resposta.status_code == 200
    assert resposta.json()["recommendedService"] == "basicUnit"


def testeTriagemRejeitaSintomasCurtos(cliente):
    resposta = cliente.post("/triage", json={**requisicaoValida, "symptoms": "dor"})
    assert resposta.status_code == 422
    assert "message" in resposta.json()


def testeTriagemRejeitaSinalDesconhecido(cliente):
    resposta = cliente.post("/triage", json={**requisicaoValida, "warningSigns": ["invented"]})
    assert resposta.status_code == 422


def testeTempoEsgotadoTemMensagemAmigavel(cliente):
    sobrescreverGerador(levantarTempoEsgotado)
    resposta = cliente.post("/triage", json=requisicaoValida)
    assert resposta.status_code == 504
    assert "demorou" in resposta.json()["message"]


def testeProvedorForaDoAr(cliente):
    sobrescreverGerador(levantarIndisponivel)
    resposta = cliente.post("/triage", json=requisicaoValida)
    assert resposta.status_code == 503


def testeRespostaInvalidaDoModelo(cliente):
    sobrescreverGerador(lambda promptSistema, promptUsuario: {"foo": "bar"})
    resposta = cliente.post("/triage", json=requisicaoValida)
    assert resposta.status_code == 502


def testeRevisaoConfirma(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    resposta = cliente.post(
        "/reviews",
        json={"recordId": criado["recordId"], "decision": "confirmed", "helpful": True},
    )
    assert resposta.status_code == 200
    assert resposta.json()["finalUrgency"] == criado["urgencyLevel"]


def testeRevisaoCorrige(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    resposta = cliente.post(
        "/reviews",
        json={"recordId": criado["recordId"], "decision": "corrected", "correctedUrgency": "high"},
    )
    assert resposta.json()["finalUrgency"] == "high"


def testeCorrecaoExigeNivel(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    resposta = cliente.post("/reviews", json={"recordId": criado["recordId"], "decision": "corrected"})
    assert resposta.status_code == 422


def testeRevisaoDeRegistroInexistente(cliente):
    resposta = cliente.post("/reviews", json={"recordId": "nope", "decision": "confirmed"})
    assert resposta.status_code == 404
