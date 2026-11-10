from fastapi import APIRouter, Depends

from app.dependencies import obterUsuarioAtual
from app.pipelines.reviewPipeline import executarRevisao
from app.schemas.reviewSchemas import ReviewRequest, ReviewResponse

roteador = APIRouter(prefix="/reviews", tags=["Revisão humana"])


@roteador.post("", response_model=ReviewResponse)
def criarRevisao(revisao: ReviewRequest, usuario=Depends(obterUsuarioAtual)):
    return executarRevisao(revisao, usuario["id"])
