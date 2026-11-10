from fastapi import APIRouter, Depends

from app.dependencies import obterBaseAssistente, obterGeradorAssistente, obterUsuarioAtual
from app.pipelines.assistantPipeline import responderPergunta
from app.schemas.assistantSchemas import AssistantRequest, AssistantResponse, TopicsResponse

roteador = APIRouter(prefix="/assistant", tags=["Assistente"])


@roteador.post("/ask", response_model=AssistantResponse)
def perguntar(
    requisicao: AssistantRequest,
    usuario=Depends(obterUsuarioAtual),
    gerar=Depends(obterGeradorAssistente),
    base=Depends(obterBaseAssistente),
):
    historico = [turno.model_dump() for turno in requisicao.history]
    return responderPergunta(requisicao.question, historico, gerar, base, tema=requisicao.topic)


@roteador.get("/topics", response_model=TopicsResponse)
def listarTemas(base=Depends(obterBaseAssistente)):
    return TopicsResponse(topics=base.temas)
