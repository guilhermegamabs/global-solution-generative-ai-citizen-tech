import httpx

from app.config import obterTempoLimite
from app.errors import CepNotFoundError, LocationUnavailableError

urlBase = "https://viacep.com.br/ws"
urlCoordenadas = "https://cep.awesomeapi.com.br/json"
cacheCoordenadas = {}


def buscarCoordenadasPorCep(cep):
    if cep in cacheCoordenadas:
        return cacheCoordenadas[cep]

    try:
        resposta = httpx.get(f"{urlCoordenadas}/{cep}", timeout=8)
        resposta.raise_for_status()
        dados = resposta.json()
        coordenadas = (float(dados["lat"]), float(dados["lng"]))
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None

    cacheCoordenadas[cep] = coordenadas
    return coordenadas


def buscarEnderecoPorCep(cep):
    try:
        resposta = httpx.get(f"{urlBase}/{cep}/json/", timeout=obterTempoLimite())
    except httpx.HTTPError:
        raise LocationUnavailableError() from None

    if resposta.status_code == 400:
        raise CepNotFoundError()
    if resposta.status_code >= 400:
        raise LocationUnavailableError()

    try:
        dados = resposta.json()
    except ValueError:
        raise LocationUnavailableError() from None

    if not isinstance(dados, dict) or dados.get("erro"):
        raise CepNotFoundError()

    return dados
