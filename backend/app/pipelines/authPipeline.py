import hashlib
import hmac
import secrets
import time
from datetime import timedelta

from app.config import obterSegredoApp
from app.errors import (
    ApiFailure,
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    InvalidCodeError,
    InvalidCredentialsError,
    ResendTooSoonError,
    TooManyAttemptsError,
    TooManyLoginAttemptsError,
)
from app.providers.codeRepository import apagarCodigo, buscarCodigo, registrarTentativa, salvarCodigo
from app.providers.databaseProvider import agora
from app.providers.sessionRepository import apagarSessao, buscarSessao, criarSessao
from app.providers.userRepository import (
    apagarUsuario,
    atualizarSenha,
    buscarUsuarioPorEmail,
    buscarUsuarioPorId,
    criarUsuario,
    marcarVerificado,
)
validadeCodigoMinutos = 10
esperaReenvioSegundos = 60
maximoTentativasCodigo = 5
validadeSessaoDias = 7
maximoFalhasLogin = 5
janelaFalhasLoginSegundos = 900
custoScrypt = 2**14
falhasLogin = {}
hashFalso = "00" * 16 + "$" + "00" * 32


def normalizarEmail(email):
    return email.strip().lower()


def gerarHashSenha(senha):
    sal = secrets.token_bytes(16)
    derivado = hashlib.scrypt(senha.encode(), salt=sal, n=custoScrypt, r=8, p=1)
    return f"{sal.hex()}${derivado.hex()}"


def conferirSenha(senha, armazenado):
    try:
        salHex, derivadoHex = armazenado.split("$")
        sal = bytes.fromhex(salHex)
        esperado = bytes.fromhex(derivadoHex)
    except ValueError:
        return False
    derivado = hashlib.scrypt(senha.encode(), salt=sal, n=custoScrypt, r=8, p=1)
    return hmac.compare_digest(derivado, esperado)


def gerarCodigo():
    return f"{secrets.randbelow(1000000):06d}"


def gerarHashCodigo(idUsuario, codigo):
    mensagem = f"{idUsuario}:{codigo}".encode()
    return hmac.new(obterSegredoApp().encode(), mensagem, hashlib.sha256).hexdigest()


def gerarHashToken(token):
    return hashlib.sha256(token.encode()).hexdigest()


def emitirCodigo(idUsuario, email, enviarEmail):
    atual = buscarCodigo(idUsuario)
    if atual and (agora() - atual["sentAt"]).total_seconds() < esperaReenvioSegundos:
        raise ResendTooSoonError()

    codigo = gerarCodigo()
    momento = agora()
    salvarCodigo(idUsuario, gerarHashCodigo(idUsuario, codigo), momento + timedelta(minutes=validadeCodigoMinutos), momento)
    try:
        enviarEmail(email, codigo)
    except ApiFailure:
        apagarCodigo(idUsuario)
        raise


def cadastrar(email, senha, enviarEmail):
    email = normalizarEmail(email)
    existente = buscarUsuarioPorEmail(email)
    if existente and existente["verified"]:
        raise EmailAlreadyRegisteredError()

    if existente:
        idUsuario = existente["id"]
        atualizarSenha(idUsuario, gerarHashSenha(senha))
    else:
        idUsuario = criarUsuario(email, gerarHashSenha(senha))

    emitirCodigo(idUsuario, email, enviarEmail)


def reenviarCodigo(email, enviarEmail):
    email = normalizarEmail(email)
    usuario = buscarUsuarioPorEmail(email)
    if usuario and not usuario["verified"]:
        emitirCodigo(usuario["id"], email, enviarEmail)


def criarSessaoUsuario(idUsuario):
    token = secrets.token_urlsafe(32)
    criarSessao(gerarHashToken(token), idUsuario, agora() + timedelta(days=validadeSessaoDias))
    return token


def verificarCodigo(email, codigo):
    email = normalizarEmail(email)
    usuario = buscarUsuarioPorEmail(email)
    if not usuario or usuario["verified"]:
        raise InvalidCodeError()

    idUsuario = usuario["id"]
    atual = buscarCodigo(idUsuario)
    if not atual:
        raise InvalidCodeError()

    if atual["expiresAt"] < agora():
        apagarCodigo(idUsuario)
        raise InvalidCodeError()

    if atual["attempts"] >= maximoTentativasCodigo:
        apagarCodigo(idUsuario)
        raise TooManyAttemptsError()

    if not hmac.compare_digest(atual["codeHash"], gerarHashCodigo(idUsuario, codigo)):
        registrarTentativa(idUsuario)
        raise InvalidCodeError()

    marcarVerificado(idUsuario)
    apagarCodigo(idUsuario)
    return criarSessaoUsuario(idUsuario), email


def registrarFalhaLogin(email):
    agoraSegundos = time.time()
    recentes = [momento for momento in falhasLogin.get(email, []) if agoraSegundos - momento < janelaFalhasLoginSegundos]
    recentes.append(agoraSegundos)
    falhasLogin[email] = recentes


def conferirBloqueioLogin(email):
    agoraSegundos = time.time()
    recentes = [momento for momento in falhasLogin.get(email, []) if agoraSegundos - momento < janelaFalhasLoginSegundos]
    if len(recentes) >= maximoFalhasLogin:
        raise TooManyLoginAttemptsError()


def entrar(email, senha):
    email = normalizarEmail(email)
    conferirBloqueioLogin(email)

    usuario = buscarUsuarioPorEmail(email)
    senhaCorreta = conferirSenha(senha, usuario["passwordHash"] if usuario else hashFalso)
    if not usuario or not senhaCorreta:
        registrarFalhaLogin(email)
        raise InvalidCredentialsError()

    if not usuario["verified"]:
        raise EmailNotVerifiedError()

    falhasLogin.pop(email, None)
    return criarSessaoUsuario(usuario["id"]), email


def obterUsuarioPorToken(token):
    hashToken = gerarHashToken(token)
    sessao = buscarSessao(hashToken)
    if not sessao:
        return None
    if sessao["expiresAt"] < agora():
        apagarSessao(hashToken)
        return None
    return buscarUsuarioPorId(sessao["userId"])


def sair(token):
    apagarSessao(gerarHashToken(token))


def apagarConta(idUsuario):
    apagarUsuario(idUsuario)
