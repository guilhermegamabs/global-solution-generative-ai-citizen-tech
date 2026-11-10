from datetime import timedelta

from sqlalchemy import select, update

from app.errors import EmailUnavailableError
from app.providers.databaseProvider import agora, obterMotor, tabelaCodigos, tabelaSessoes, tabelaUsuarios
from conftest import (
    autenticar,
    cadastrarEVerificar,
    codigosEnviados,
    requisicaoValida,
    senhaPadrao,
    sobrescreverEnviadorEmail,
    ultimoCodigo,
)

email = "ana@exemplo.com"


def cadastrar(cliente, endereco=email, senha=senhaPadrao):
    return cliente.post("/auth/register", json={"email": endereco, "password": senha})


def envelhecerCodigo(minutos):
    with obterMotor().begin() as conexao:
        conexao.execute(
            update(tabelaCodigos).values(
                sentAt=agora() - timedelta(minutes=minutos),
                expiresAt=agora() - timedelta(minutes=minutos) + timedelta(minutes=10),
            )
        )


def testeCadastroEnviaCodigoDeSeisDigitos(clienteAnonimo):
    resposta = cadastrar(clienteAnonimo)
    assert resposta.status_code == 200
    assert len(codigosEnviados) == 1
    assert len(codigosEnviados[0][1]) == 6 and codigosEnviados[0][1].isdigit()


def testeVerificarCodigoCriaSessaoEPermiteUsarAConta(clienteAnonimo):
    cadastrar(clienteAnonimo)
    resposta = clienteAnonimo.post("/auth/verify", json={"email": email, "code": ultimoCodigo(email)})
    assert resposta.status_code == 200
    autenticar(clienteAnonimo, resposta.json()["token"])
    assert clienteAnonimo.get("/auth/me").json() == {"email": email}


def testeEmailJaVerificadoRetorna409(clienteAnonimo):
    cadastrarEVerificar(clienteAnonimo)
    assert cadastrar(clienteAnonimo).status_code == 409


def testeEmailEUnicoIgnorandoMaiusculas(clienteAnonimo):
    cadastrarEVerificar(clienteAnonimo)
    assert cadastrar(clienteAnonimo, "ANA@Exemplo.COM").status_code == 409


def testeSenhaNaoFicaEmTextoPuro(clienteAnonimo):
    cadastrar(clienteAnonimo)
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaUsuarios)).first()
    assert linha._mapping["passwordHash"] != senhaPadrao
    assert senhaPadrao not in linha._mapping["passwordHash"]


def testeCodigoNaoFicaEmTextoPuro(clienteAnonimo):
    cadastrar(clienteAnonimo)
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaCodigos)).first()
    assert linha._mapping["codeHash"] != ultimoCodigo(email)


def testeLoginAntesDeVerificarRetorna403(clienteAnonimo):
    cadastrar(clienteAnonimo)
    resposta = clienteAnonimo.post("/auth/login", json={"email": email, "password": senhaPadrao})
    assert resposta.status_code == 403
    assert resposta.json()["code"] == "emailNotVerified"


def testeLoginAposVerificar(clienteAnonimo):
    cadastrarEVerificar(clienteAnonimo)
    resposta = clienteAnonimo.post("/auth/login", json={"email": "ANA@exemplo.com", "password": senhaPadrao})
    assert resposta.status_code == 200
    assert resposta.json()["email"] == email


def testeLoginComSenhaErradaRetorna401(clienteAnonimo):
    cadastrarEVerificar(clienteAnonimo)
    resposta = clienteAnonimo.post("/auth/login", json={"email": email, "password": "outraSenha99"})
    assert resposta.status_code == 401
    assert "incorretos" in resposta.json()["message"]


def testeLoginDeEmailInexistenteTemMesmaMensagem(clienteAnonimo):
    resposta = clienteAnonimo.post("/auth/login", json={"email": "ninguem@exemplo.com", "password": senhaPadrao})
    assert resposta.status_code == 401
    assert "incorretos" in resposta.json()["message"]


def testeBloqueiaLoginAposCincoFalhas(clienteAnonimo):
    cadastrarEVerificar(clienteAnonimo)
    for tentativa in range(5):
        clienteAnonimo.post("/auth/login", json={"email": email, "password": "errada12345"})
    resposta = clienteAnonimo.post("/auth/login", json={"email": email, "password": senhaPadrao})
    assert resposta.status_code == 429


def testeCodigoErradoNaoVerifica(clienteAnonimo):
    cadastrar(clienteAnonimo)
    resposta = clienteAnonimo.post("/auth/verify", json={"email": email, "code": "000000"})
    assert resposta.status_code == 400


def testeCincoErrosInvalidamOCodigo(clienteAnonimo):
    cadastrar(clienteAnonimo)
    certo = ultimoCodigo(email)
    errado = "000000" if certo != "000000" else "111111"
    for tentativa in range(5):
        clienteAnonimo.post("/auth/verify", json={"email": email, "code": errado})
    resposta = clienteAnonimo.post("/auth/verify", json={"email": email, "code": certo})
    assert resposta.status_code == 429


def testeCodigoVencidoERejeitado(clienteAnonimo):
    cadastrar(clienteAnonimo)
    envelhecerCodigo(30)
    resposta = clienteAnonimo.post("/auth/verify", json={"email": email, "code": ultimoCodigo(email)})
    assert resposta.status_code == 400


def testeReenvioRespeitaEspera(clienteAnonimo):
    cadastrar(clienteAnonimo)
    assert clienteAnonimo.post("/auth/resend", json={"email": email}).status_code == 429
    envelhecerCodigo(2)
    primeiro = ultimoCodigo(email)
    assert clienteAnonimo.post("/auth/resend", json={"email": email}).status_code == 200
    assert len(codigosEnviados) == 2
    segundo = ultimoCodigo(email)
    if primeiro != segundo:
        assert clienteAnonimo.post("/auth/verify", json={"email": email, "code": primeiro}).status_code == 400
    assert clienteAnonimo.post("/auth/verify", json={"email": email, "code": segundo}).status_code == 200


def testeReenvioParaEmailDesconhecidoNaoRevelaNada(clienteAnonimo):
    resposta = clienteAnonimo.post("/auth/resend", json={"email": "ninguem@exemplo.com"})
    assert resposta.status_code == 200
    assert codigosEnviados == []


def testeFalhaNoEnvioDoEmailPermiteTentarDeNovo(clienteAnonimo):
    def falhar(destino, codigo):
        raise EmailUnavailableError()

    sobrescreverEnviadorEmail(falhar)
    assert cadastrar(clienteAnonimo).status_code == 503
    from conftest import enviadorFalso

    sobrescreverEnviadorEmail(enviadorFalso)
    assert cadastrar(clienteAnonimo).status_code == 200


def testeSenhaCurtaERejeitada(clienteAnonimo):
    assert cadastrar(clienteAnonimo, senha="curta").status_code == 422


def testeEmailInvalidoERejeitado(clienteAnonimo):
    assert cadastrar(clienteAnonimo, endereco="sem-arroba").status_code == 422


def testeTriagemExigeLogin(clienteAnonimo):
    resposta = clienteAnonimo.post("/triage", json=requisicaoValida)
    assert resposta.status_code == 401
    assert resposta.json()["code"] == "sessionExpired"


def testeTokenInvalidoRetorna401(clienteAnonimo):
    autenticar(clienteAnonimo, "token-falso")
    assert clienteAnonimo.get("/history").status_code == 401


def testeSessaoExpiradaRetorna401(cliente):
    with obterMotor().begin() as conexao:
        conexao.execute(update(tabelaSessoes).values(expiresAt=agora() - timedelta(days=1)))
    assert cliente.get("/auth/me").status_code == 401


def testeLogoutInvalidaOToken(cliente):
    assert cliente.post("/auth/logout").status_code == 200
    assert cliente.get("/auth/me").status_code == 401


def testeHistoricoGuardaTriagensDoUsuario(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    registros = cliente.get("/history").json()["records"]
    assert [registro["recordId"] for registro in registros] == [criado["recordId"]]
    assert registros[0]["review"] is None


def testeHistoricoNaoGuardaORelatoDigitado(cliente):
    cliente.post("/triage", json=requisicaoValida)
    with obterMotor().connect() as conexao:
        colunas = conexao.execute(select(tabelaUsuarios.metadata.tables["triageRecords"])).keys()
    assert "symptoms" not in list(colunas)


def testeHistoricoIncluiRevisao(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    cliente.post("/reviews", json={"recordId": criado["recordId"], "decision": "corrected", "correctedUrgency": "high", "helpful": False})
    revisao = cliente.get("/history").json()["records"][0]["review"]
    assert revisao == {"decision": "corrected", "finalUrgency": "high", "helpful": False}


def testeHistoricoEIsoladoEntreUsuarios(cliente):
    cliente.post("/triage", json=requisicaoValida)
    outro = cadastrarEVerificar(cliente, "bia@exemplo.com")
    autenticar(cliente, outro)
    assert cliente.get("/history").json()["records"] == []


def testeNaoRevisaRegistroDeOutroUsuario(cliente):
    criado = cliente.post("/triage", json=requisicaoValida).json()
    autenticar(cliente, cadastrarEVerificar(cliente, "bia@exemplo.com"))
    resposta = cliente.post("/reviews", json={"recordId": criado["recordId"], "decision": "confirmed"})
    assert resposta.status_code == 404


def testeApagarContaRemoveUsuarioEHistorico(cliente):
    cliente.post("/triage", json=requisicaoValida)
    assert cliente.delete("/auth/account").status_code == 200
    assert cliente.get("/auth/me").status_code == 401
    resposta = cliente.post("/auth/login", json={"email": email, "password": senhaPadrao})
    assert resposta.status_code == 401
    with obterMotor().connect() as conexao:
        total = conexao.execute(select(tabelaUsuarios.metadata.tables["triageRecords"])).all()
    assert total == []
