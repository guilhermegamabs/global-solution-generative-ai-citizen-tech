from fastapi import APIRouter, Depends

from app.dependencies import obterFontesLocalizacao
from app.pipelines.unitsPipeline import buscarUpasProximas
from app.schemas.unitsSchemas import UnitsRequest, UnitsResponse

roteador = APIRouter(prefix="/units", tags=["UPAs próximas"])


@roteador.post("/nearby", response_model=UnitsResponse)
def listarUpasProximas(requisicao: UnitsRequest, fontes=Depends(obterFontesLocalizacao)):
    return buscarUpasProximas(requisicao, fontes)
