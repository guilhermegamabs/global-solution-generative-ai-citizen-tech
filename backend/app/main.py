import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import deveAquecerRag, obterOrigensPermitidas
from app.errors import ApiFailure
from app.rag.knowledgeBase import aquecerRag
from app.routers import (
    assistantRouter,
    authRouter,
    healthRouter,
    historyRouter,
    metaRouter,
    reviewRouter,
    triageRouter,
    unitsRouter,
)


@asynccontextmanager
async def cicloDeVida(app: FastAPI):
    if deveAquecerRag():
        await asyncio.to_thread(aquecerRag)
    yield


aplicacao = FastAPI(title="Orienta Saúde API", version="1.1.0", lifespan=cicloDeVida)

aplicacao.add_middleware(
    CORSMiddleware,
    allow_origins=obterOrigensPermitidas(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

aplicacao.include_router(healthRouter.roteador)
aplicacao.include_router(authRouter.roteador)
aplicacao.include_router(historyRouter.roteador)
aplicacao.include_router(metaRouter.roteador)
aplicacao.include_router(triageRouter.roteador)
aplicacao.include_router(reviewRouter.roteador)
aplicacao.include_router(unitsRouter.roteador)
aplicacao.include_router(assistantRouter.roteador)


@aplicacao.exception_handler(ApiFailure)
async def tratarFalha(requisicao: Request, erro: ApiFailure):
    conteudo = {"message": erro.mensagemUsuario}
    if erro.codigoErro:
        conteudo["code"] = erro.codigoErro
    return JSONResponse(status_code=erro.codigoStatus, content=conteudo)


@aplicacao.exception_handler(RequestValidationError)
async def tratarEntradaInvalida(requisicao: Request, erro: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Confira os dados informados e tente novamente."},
    )
