import math
from concurrent.futures import ThreadPoolExecutor

from app.errors import LocationUnavailableError, NoUnitsFoundError
from app.schemas.unitsSchemas import NearbyUnit, UnitsOrigin, UnitsResponse

raioTerraKm = 6371.0
limiteDivergenciaKm = 1.5
limiteRefinoKm = 5.0
margemCandidatas = 5


def calcularDistanciaKm(latitudeA, longitudeA, latitudeB, longitudeB):
    deltaLatitude = math.radians(latitudeB - latitudeA)
    deltaLongitude = math.radians(longitudeB - longitudeA)
    parcela = (
        math.sin(deltaLatitude / 2) ** 2
        + math.cos(math.radians(latitudeA))
        * math.cos(math.radians(latitudeB))
        * math.sin(deltaLongitude / 2) ** 2
    )
    return 2 * raioTerraKm * math.asin(math.sqrt(parcela))


def marcarPosicaoIncerta(unidades, buscarCoordenadas):
    ceps = [unidade.get("cep") for unidade in unidades]
    with ThreadPoolExecutor(max_workers=5) as executor:
        achadas = list(executor.map(lambda cep: buscarCoordenadas(cep) if cep else None, ceps))

    marcadas = []
    for unidade, achada in zip(unidades, achadas):
        divergencia = 0.0
        if achada:
            divergencia = calcularDistanciaKm(unidade["latitude"], unidade["longitude"], achada[0], achada[1])
        marcadas.append({**unidade, "positionUncertain": divergencia > limiteDivergenciaKm})
    return marcadas


def refinarPosicoes(unidades, latitude, longitude, cidade, estado, buscarPonto):
    refinadas = []
    for unidade in unidades:
        if not unidade["positionUncertain"]:
            refinadas.append(unidade)
            continue

        ponto = buscarPonto(unidade["name"], cidade, estado)
        proximoDoCadastro = ponto and calcularDistanciaKm(unidade["latitude"], unidade["longitude"], ponto[0], ponto[1]) <= limiteRefinoKm
        if not proximoDoCadastro:
            refinadas.append(unidade)
            continue

        refinadas.append(
            {
                **unidade,
                "latitude": ponto[0],
                "longitude": ponto[1],
                "distanceKm": round(calcularDistanciaKm(latitude, longitude, ponto[0], ponto[1]), 1),
                "positionUncertain": False,
            }
        )
    return refinadas


def buscarUpasProximas(requisicao, fontes):
    cep = requisicao.cep.replace("-", "")
    endereco = fontes["buscarCep"](cep)

    codigoIbge = str(endereco.get("ibge") or "")
    if len(codigoIbge) < 6:
        raise LocationUnavailableError()

    latitude, longitude, aproximado = fontes["geocodificar"](endereco)
    unidades = fontes["listarUnidades"](codigoIbge[:6])
    if not unidades:
        raise NoUnitsFoundError()

    comDistancia = [
        {
            **unidade,
            "distanceKm": round(
                calcularDistanciaKm(latitude, longitude, unidade["latitude"], unidade["longitude"]), 1
            ),
        }
        for unidade in unidades
    ]
    candidatas = sorted(comDistancia, key=lambda unidade: unidade["distanceKm"])[: requisicao.limit + margemCandidatas]
    marcadas = marcarPosicaoIncerta(candidatas, fontes["coordenadasPorCep"])
    refinadas = refinarPosicoes(
        marcadas, latitude, longitude, endereco.get("localidade", ""), endereco.get("uf", ""), fontes["pontoPorNome"]
    )
    maisProximas = sorted(refinadas, key=lambda unidade: unidade["distanceKm"])[: requisicao.limit]

    return UnitsResponse(
        origin=UnitsOrigin(
            latitude=latitude,
            longitude=longitude,
            city=endereco.get("localidade", ""),
            state=endereco.get("uf", ""),
            neighborhood=endereco.get("bairro", ""),
            approximate=aproximado,
        ),
        units=[NearbyUnit(**unidade) for unidade in maisProximas],
    )
