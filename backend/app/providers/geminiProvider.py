import json
import logging
import time

import httpx

from app.config import obterChaveGemini, obterModeloGemini, obterTempoLimite
from app.errors import (
    InvalidModelResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

urlBase = "https://generativelanguage.googleapis.com/v1beta/models"
statusTransitorios = (429, 500, 502, 503, 504)
tentativasMaximas = 3
pausaBase = 2
diario = logging.getLogger("orienta.gemini")

esquemaResposta = {
    "type": "OBJECT",
    "properties": {
        "urgencyLevel": {
            "type": "STRING",
            "enum": ["low", "medium", "high", "emergency"],
        },
        "recommendedService": {
            "type": "STRING",
            "enum": ["selfCare", "basicUnit", "urgentCare", "ambulance"],
        },
        "summary": {"type": "STRING"},
        "guidance": {"type": "ARRAY", "items": {"type": "STRING"}},
        "warningSignsToWatch": {"type": "ARRAY", "items": {"type": "STRING"}},
        "rationale": {"type": "STRING"},
    },
    "required": [
        "urgencyLevel",
        "recommendedService",
        "summary",
        "guidance",
        "warningSignsToWatch",
        "rationale",
    ],
}


def enviarComRepeticao(corpo, chaveApi, modelo=None):
    for tentativa in range(tentativasMaximas):
        try:
            resposta = httpx.post(
                f"{urlBase}/{modelo or obterModeloGemini()}:generateContent",
                json=corpo,
                headers={"x-goog-api-key": chaveApi},
                timeout=obterTempoLimite(),
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError() from None
        except httpx.HTTPError:
            raise ProviderUnavailableError() from None

        ultima = tentativa == tentativasMaximas - 1
        if resposta.status_code in statusTransitorios and not ultima:
            diario.warning("Gemini respondeu %s; nova tentativa %s", resposta.status_code, tentativa + 2)
            time.sleep(pausaBase * (tentativa + 1))
            continue
        return resposta


def extrairTexto(corpoResposta):
    partes = corpoResposta["candidates"][0]["content"]["parts"]
    return "".join(parte.get("text", "") for parte in partes if not parte.get("thought"))


def gerarJson(promptSistema, promptUsuario, esquema, modelo=None, temperatura=0.2):
    chaveApi = obterChaveGemini()
    if not chaveApi:
        raise ProviderUnavailableError()

    corpo = {
        "systemInstruction": {"parts": [{"text": promptSistema}]},
        "contents": [{"role": "user", "parts": [{"text": promptUsuario}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": esquema,
            "temperature": temperatura,
        },
    }

    resposta = enviarComRepeticao(corpo, chaveApi, modelo)

    if resposta.status_code >= 400:
        diario.error("Gemini recusou a chamada (status %s)", resposta.status_code)
        raise ProviderUnavailableError()

    try:
        return json.loads(extrairTexto(resposta.json()))
    except (KeyError, IndexError, TypeError, ValueError):
        raise InvalidModelResponseError() from None


def gerarEstruturado(promptSistema, promptUsuario):
    return gerarJson(promptSistema, promptUsuario, esquemaResposta)
