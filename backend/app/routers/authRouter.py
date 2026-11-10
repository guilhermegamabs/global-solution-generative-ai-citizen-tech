from fastapi import APIRouter, Depends

from app.dependencies import obterEnviadorEmail, obterTokenBearer, obterUsuarioAtual
from app.pipelines import authPipeline
from app.schemas.authSchemas import (
    LoginRequest,
    MeResponse,
    MessageResponse,
    RegisterRequest,
    ResendRequest,
    SessionResponse,
    VerifyRequest,
)

roteador = APIRouter(prefix="/auth", tags=["Conta e autenticação"])

mensagemCodigoEnviado = "Se o e-mail puder ser confirmado, enviamos um código de 6 números para ele."


@roteador.post("/register", response_model=MessageResponse)
def criarConta(requisicao: RegisterRequest, enviarEmail=Depends(obterEnviadorEmail)):
    authPipeline.cadastrar(requisicao.email, requisicao.password, enviarEmail)
    return MessageResponse(message=mensagemCodigoEnviado)


@roteador.post("/resend", response_model=MessageResponse)
def reenviarCodigo(requisicao: ResendRequest, enviarEmail=Depends(obterEnviadorEmail)):
    authPipeline.reenviarCodigo(requisicao.email, enviarEmail)
    return MessageResponse(message=mensagemCodigoEnviado)


@roteador.post("/verify", response_model=SessionResponse)
def confirmarCodigo(requisicao: VerifyRequest):
    token, email = authPipeline.verificarCodigo(requisicao.email, requisicao.code)
    return SessionResponse(token=token, email=email)


@roteador.post("/login", response_model=SessionResponse)
def entrarNaConta(requisicao: LoginRequest):
    token, email = authPipeline.entrar(requisicao.email, requisicao.password)
    return SessionResponse(token=token, email=email)


@roteador.post("/logout", response_model=MessageResponse)
def sairDaConta(token: str = Depends(obterTokenBearer)):
    authPipeline.sair(token)
    return MessageResponse(message="Você saiu da conta.")


@roteador.get("/me", response_model=MeResponse)
def obterConta(usuario=Depends(obterUsuarioAtual)):
    return MeResponse(email=usuario["email"])


@roteador.delete("/account", response_model=MessageResponse)
def apagarConta(usuario=Depends(obterUsuarioAtual)):
    authPipeline.apagarConta(usuario["id"])
    return MessageResponse(message="Sua conta e seu histórico foram apagados.")
