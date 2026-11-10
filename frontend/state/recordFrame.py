import pandas as pd

colunasTabela = [
    "protocol",
    "createdAt",
    "urgencyLevel",
    "recommendedService",
    "ageRange",
    "reviewStatus",
]


def resolverStatus(registro):
    revisao = registro["review"]
    return revisao["decision"] if revisao else "pending"


def resolverUrgencia(registro):
    revisao = registro["review"]
    return revisao["finalUrgency"] if revisao else registro["urgencyLevel"]


def paraTabela(registros):
    linhas = [
        {
            "protocol": registro["protocol"],
            "createdAt": pd.to_datetime(registro["createdAt"], utc=True).tz_convert("America/Sao_Paulo"),
            "urgencyLevel": resolverUrgencia(registro),
            "recommendedService": registro["recommendedService"],
            "ageRange": registro["ageRange"],
            "reviewStatus": resolverStatus(registro),
        }
        for registro in registros
    ]
    return pd.DataFrame(linhas, columns=colunasTabela)
