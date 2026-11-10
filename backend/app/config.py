import os
import secrets

from dotenv import load_dotenv

load_dotenv()

segredoGerado = secrets.token_hex(32)


def obterChaveGemini():
    return os.getenv("GEMINIAPIKEY", "")


def obterModeloGemini():
    return os.getenv("GEMINIMODEL", "gemini-2.5-flash")


def obterModeloAssistente():
    return os.getenv("ASSISTENTEMODEL", "gemini-3.5-flash-lite")


def obterOrigensPermitidas():
    bruto = os.getenv("ALLOWEDORIGINS", "http://localhost:8501")
    return [origem.strip() for origem in bruto.split(",") if origem.strip()]


def obterTempoLimite():
    return float(os.getenv("REQUESTTIMEOUT", "30"))


def obterUrlBanco():
    url = os.getenv("DATABASEURL", "sqlite:///orienta.db")
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo):]
    return url


def obterChaveBrevo():
    return os.getenv("BREVOAPIKEY", "")


def obterEmailRemetente():
    return os.getenv("SENDEREMAIL", "")


def obterNomeRemetente():
    return os.getenv("SENDERNAME", "Orienta Saúde")


def mostrarCodigoNoLog():
    return os.getenv("MOSTRARCODIGONOLOG", "").lower() == "true"


def deveAquecerRag():
    return os.getenv("AQUECERRAG", "true").lower() == "true"


def obterSegredoApp():
    return os.getenv("SEGREDOAPP") or segredoGerado
