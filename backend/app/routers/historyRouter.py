from fastapi import APIRouter, Depends

from app.dependencies import obterUsuarioAtual
from app.providers.recordRepository import listarRegistros
from app.schemas.historySchemas import HistoryResponse

roteador = APIRouter(prefix="/history", tags=["Histórico do usuário"])


@roteador.get("", response_model=HistoryResponse)
def obterHistorico(usuario=Depends(obterUsuarioAtual)):
    return HistoryResponse(records=listarRegistros(usuario["id"]))
