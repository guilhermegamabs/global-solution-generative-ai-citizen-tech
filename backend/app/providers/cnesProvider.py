import time

import httpx

from app.config import obterTempoLimite
from app.errors import UnitsUnavailableError

urlCnes = "https://apidadosabertos.saude.gov.br/cnes/estabelecimentos"
tipoPostoUpa = 73
tamanhoPagina = 20
maximoPaginas = 15
validadeCache = 6 * 3600
cacheMunicipios = {}


def normalizarUnidade(bruto):
    latitude = bruto.get("latitude_estabelecimento_decimo_grau")
    longitude = bruto.get("longitude_estabelecimento_decimo_grau")
    if latitude is None or longitude is None:
        return None
    if bruto.get("codigo_motivo_desabilitacao_estabelecimento"):
        return None

    nome = (bruto.get("nome_fantasia") or "UPA").strip()
    atendeSus = bruto.get("estabelecimento_faz_atendimento_ambulatorial_sus") == "SIM"
    if not atendeSus and not nome.upper().startswith("UPA"):
        return None

    logradouro = (bruto.get("endereco_estabelecimento") or "").title()
    numero = bruto.get("numero_estabelecimento") or "s/n"
    turno = (bruto.get("descricao_turno_atendimento") or "").upper()

    return {
        "name": nome,
        "cep": str(bruto.get("codigo_cep_estabelecimento") or ""),
        "address": f"{logradouro}, {numero}".strip(", "),
        "neighborhood": (bruto.get("bairro_estabelecimento") or "").title(),
        "phone": bruto.get("numero_telefone_estabelecimento"),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "open24h": "24 HORAS" in turno,
    }


def buscarPagina(codigoMunicipio, deslocamento):
    try:
        resposta = httpx.get(
            urlCnes,
            params={
                "codigo_tipo_unidade": tipoPostoUpa,
                "codigo_municipio": codigoMunicipio,
                "limit": tamanhoPagina,
                "offset": deslocamento,
            },
            timeout=obterTempoLimite(),
        )
        resposta.raise_for_status()
        return resposta.json()["estabelecimentos"]
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise UnitsUnavailableError() from None


def listarUpasDoMunicipio(codigoMunicipio):
    guardado = cacheMunicipios.get(codigoMunicipio)
    if guardado and time.time() - guardado[0] < validadeCache:
        return guardado[1]

    unidades = []
    for pagina in range(maximoPaginas):
        lote = buscarPagina(codigoMunicipio, pagina * tamanhoPagina)
        for bruto in lote:
            unidade = normalizarUnidade(bruto)
            if unidade:
                unidades.append(unidade)
        if len(lote) < tamanhoPagina:
            break

    cacheMunicipios[codigoMunicipio] = (time.time(), unidades)
    return unidades
