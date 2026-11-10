import logging

import httpx

from app.config import (
    mostrarCodigoNoLog,
    obterChaveBrevo,
    obterEmailRemetente,
    obterNomeRemetente,
    obterTempoLimite,
)
from app.errors import EmailUnavailableError

urlBrevo = "https://api.brevo.com/v3/smtp/email"
diario = logging.getLogger("orienta.email")


def montarHtmlCodigo(codigo):
    return (
        "<div style='font-family:Arial,sans-serif;color:#0F2A43'>"
        "<h2 style='color:#073B6B'>Orienta Saúde</h2>"
        "<p>Use este código para confirmar o seu e-mail:</p>"
        f"<p style='font-size:32px;font-weight:bold;letter-spacing:6px;color:#0B5FA5'>{codigo}</p>"
        "<p>O código vale por 10 minutos. Se você não pediu, ignore este e-mail.</p>"
        "</div>"
    )


def extrairMotivo(resposta):
    try:
        dados = resposta.json()
        return f'{dados.get("code")}: {dados.get("message")}'
    except (ValueError, AttributeError):
        return "sem detalhes na resposta"


def enviarCodigoPorEmail(destino, codigo):
    if mostrarCodigoNoLog():
        print(f"Código de verificação para {destino}: {codigo}")
        return

    chave = obterChaveBrevo()
    remetente = obterEmailRemetente()
    if not chave or not remetente:
        diario.error("Envio de e-mail não configurado: preencha BREVOAPIKEY e SENDEREMAIL no .env")
        raise EmailUnavailableError()

    corpo = {
        "sender": {"name": obterNomeRemetente(), "email": remetente},
        "to": [{"email": destino}],
        "subject": "Seu código de verificação - Orienta Saúde",
        "htmlContent": montarHtmlCodigo(codigo),
    }

    try:
        resposta = httpx.post(
            urlBrevo,
            json=corpo,
            headers={"api-key": chave, "accept": "application/json"},
            timeout=obterTempoLimite(),
        )
    except httpx.HTTPError as erro:
        diario.error("Não foi possível falar com a Brevo: %s", type(erro).__name__)
        raise EmailUnavailableError() from None

    if resposta.status_code >= 400:
        diario.error("A Brevo recusou o envio (status %s): %s", resposta.status_code, extrairMotivo(resposta))
        raise EmailUnavailableError()
