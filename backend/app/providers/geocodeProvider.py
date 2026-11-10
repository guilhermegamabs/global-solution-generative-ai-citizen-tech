import time

import httpx

from app.config import obterTempoLimite
from app.errors import LocationUnavailableError

urlBusca = "https://nominatim.openstreetmap.org/search"
agenteUsuario = "OrientaSaudeGS/1.0 (projeto academico FIAP)"
pausaEntreConsultas = 1.1


marcadoresHonorificos = (" DR ", " DRA ", " PROF ", " PROFA ", " DOM ", " DONA ", " VEREADOR ", " DEPUTADO ")
classesDeSaude = ("amenity", "healthcare")
cachePontos = {}


def simplificarNome(nome):
    texto = f" {nome.upper()} "
    corte = len(texto)
    for marcador in marcadoresHonorificos:
        posicao = texto.find(marcador)
        if posicao > 0:
            corte = min(corte, posicao)
    return texto[:corte].strip().title()


def escolherPonto(achados, cidade):
    for achado in achados:
        eDeSaude = achado.get("class") in classesDeSaude
        naCidade = cidade.lower() in achado.get("display_name", "").lower()
        if eDeSaude and naCidade:
            try:
                return float(achado["lat"]), float(achado["lon"])
            except (KeyError, TypeError, ValueError):
                return None
    return None


def buscarPontoPorNome(nome, cidade, estado):
    chave = (nome, cidade, estado)
    if chave in cachePontos:
        return cachePontos[chave]

    time.sleep(pausaEntreConsultas)
    try:
        resposta = httpx.get(
            urlBusca,
            params={"q": f"{simplificarNome(nome)}, {cidade}, {estado}, Brasil", "format": "json", "limit": 5},
            headers={"User-Agent": agenteUsuario},
            timeout=obterTempoLimite(),
        )
        resposta.raise_for_status()
        ponto = escolherPonto(resposta.json(), cidade)
    except (httpx.HTTPError, ValueError):
        return None

    cachePontos[chave] = ponto
    return ponto


def montarConsultas(endereco):
    cidade = endereco.get("localidade", "")
    estado = endereco.get("uf", "")
    logradouro = endereco.get("logradouro", "")
    consultas = []
    if logradouro:
        consultas.append(
            ({"street": logradouro, "city": cidade, "state": estado, "country": "Brazil"}, False)
        )
    consultas.append(({"city": cidade, "state": estado, "country": "Brazil"}, True))
    return consultas


def consultarNominatim(parametros):
    try:
        resposta = httpx.get(
            urlBusca,
            params={**parametros, "format": "json", "limit": 1},
            headers={"User-Agent": agenteUsuario},
            timeout=obterTempoLimite(),
        )
        resposta.raise_for_status()
        achados = resposta.json()
    except (httpx.HTTPError, ValueError):
        raise LocationUnavailableError() from None

    if not achados:
        return None

    try:
        return float(achados[0]["lat"]), float(achados[0]["lon"])
    except (KeyError, TypeError, ValueError):
        return None


def geocodificar(endereco):
    for posicao, (parametros, aproximado) in enumerate(montarConsultas(endereco)):
        if posicao > 0:
            time.sleep(pausaEntreConsultas)
        achado = consultarNominatim(parametros)
        if achado:
            return achado[0], achado[1], aproximado
    raise LocationUnavailableError()
