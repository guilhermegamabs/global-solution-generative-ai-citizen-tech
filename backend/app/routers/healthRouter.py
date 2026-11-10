from fastapi import APIRouter

roteador = APIRouter(prefix="/health", tags=["Disponibilidade"])


@roteador.get("")
def verificarSaude():
    return {"status": "ok"}
