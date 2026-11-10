from fastapi import Depends, Header

from app.config import obterModeloAssistente
from app.errors import AuthRequiredError
from app.pipelines.authPipeline import obterUsuarioPorToken
from app.providers.cepProvider import buscarCoordenadasPorCep, buscarEnderecoPorCep
from app.providers.cnesProvider import listarUpasDoMunicipio
from app.providers.emailProvider import enviarCodigoPorEmail
from app.providers.geminiProvider import gerarEstruturado, gerarJson
from app.providers.geocodeProvider import buscarPontoPorNome, geocodificar
from app.rag.knowledgeBase import obterBaseConhecimento
from app.rag.prompts import esquemaResposta


def obterGerador():
    return gerarEstruturado


def gerarRespostaAssistente(promptSistema, promptUsuario):
    return gerarJson(promptSistema, promptUsuario, esquemaResposta, modelo=obterModeloAssistente())


def obterGeradorAssistente():
    return gerarRespostaAssistente


def obterBaseAssistente():
    return obterBaseConhecimento()


def obterEnviadorEmail():
    return enviarCodigoPorEmail


def obterFontesLocalizacao():
    return {
        "buscarCep": buscarEnderecoPorCep,
        "geocodificar": geocodificar,
        "listarUnidades": listarUpasDoMunicipio,
        "coordenadasPorCep": buscarCoordenadasPorCep,
        "pontoPorNome": buscarPontoPorNome,
    }


def obterTokenBearer(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthRequiredError()
    return authorization[len("Bearer "):]


def obterUsuarioAtual(token: str = Depends(obterTokenBearer)):
    usuario = obterUsuarioPorToken(token)
    if not usuario:
        raise AuthRequiredError()
    return usuario
