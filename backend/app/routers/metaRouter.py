from fastapi import APIRouter

from app.pipelines.catalog import rotulosDuracao, rotulosFaixaEtaria, rotulosSinaisAlerta
from app.schemas.metaSchemas import OptionItem, OptionsResponse

roteador = APIRouter(prefix="/meta", tags=["Opções do formulário"])


def paraItens(rotulos):
    return [OptionItem(value=chave.value, label=rotulo) for chave, rotulo in rotulos.items()]


@roteador.get("/options", response_model=OptionsResponse)
def obterOpcoes():
    return OptionsResponse(
        ageRanges=paraItens(rotulosFaixaEtaria),
        durations=paraItens(rotulosDuracao),
        warningSigns=paraItens(rotulosSinaisAlerta),
    )
