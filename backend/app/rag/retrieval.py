import math
from dataclasses import dataclass

import numpy as np
from rank_bm25 import BM25Okapi

from app.providers.embeddingProvider import codificarConsulta, codificarPassagens, pontuarPares
from app.rag.textUtils import tokenizar

constanteRrf = 60
candidatosPorBusca = 30
candidatosRerank = 20


@dataclass
class Resultado:
    trecho: object
    pontuacao: float
    origem: str


def sigmoide(valor):
    return 1 / (1 + math.exp(-valor))


class BuscaLexical:
    nome = "bm25"

    def __init__(self, trechos):
        self.trechos = trechos
        self.indice = BM25Okapi([tokenizar(trecho.textoIndexado) for trecho in trechos])

    def buscar(self, consulta, k, permitidos=None):
        pontuacoes = self.indice.get_scores(tokenizar(consulta))
        ordem = np.argsort(-pontuacoes)
        resultados = []
        for posicao in ordem:
            if permitidos is not None and posicao not in permitidos:
                continue
            if pontuacoes[posicao] <= 0:
                break
            resultados.append(Resultado(self.trechos[posicao], float(pontuacoes[posicao]), self.nome))
            if len(resultados) == k:
                break
        return resultados


class BuscaDensa:
    nome = "denso"

    def __init__(self, trechos):
        self.trechos = trechos
        self.vetores = codificarPassagens([trecho.textoIndexado for trecho in trechos])

    def buscar(self, consulta, k, permitidos=None):
        similaridades = self.vetores @ codificarConsulta(consulta)
        ordem = np.argsort(-similaridades)
        resultados = []
        for posicao in ordem:
            if permitidos is not None and posicao not in permitidos:
                continue
            resultados.append(Resultado(self.trechos[posicao], float(similaridades[posicao]), self.nome))
            if len(resultados) == k:
                break
        return resultados


class BuscaHibrida:
    nome = "hibrido"

    def __init__(self, trechos, lexical=None, densa=None):
        self.trechos = trechos
        self.lexical = lexical or BuscaLexical(trechos)
        self.densa = densa or BuscaDensa(trechos)

    def buscar(self, consulta, k, permitidos=None):
        combinados = {}
        for busca in (self.lexical, self.densa):
            for posicao, resultado in enumerate(busca.buscar(consulta, candidatosPorBusca, permitidos)):
                chave = resultado.trecho.chunkId
                anterior = combinados.get(chave, (resultado.trecho, 0.0))
                combinados[chave] = (anterior[0], anterior[1] + 1 / (constanteRrf + posicao + 1))
        ordenados = sorted(combinados.values(), key=lambda par: -par[1])[:k]
        return [Resultado(trecho, pontuacao, self.nome) for trecho, pontuacao in ordenados]


class BuscaComRerank:
    def __init__(self, base):
        self.base = base
        self.nome = f"{base.nome}Rerank"

    def buscar(self, consulta, k, permitidos=None):
        candidatos = self.base.buscar(consulta, candidatosRerank, permitidos)
        if not candidatos:
            return []
        logits = pontuarPares(consulta, [resultado.trecho.textoIndexado for resultado in candidatos])
        ordem = np.argsort(-logits)[:k]
        return [Resultado(candidatos[posicao].trecho, sigmoide(float(logits[posicao])), self.nome) for posicao in ordem]


def construirBuscador(nome, trechos, cache=None):
    cache = cache if cache is not None else {}
    if "bm25" not in cache:
        cache["bm25"] = BuscaLexical(trechos)
    if nome == "bm25":
        return cache["bm25"]
    if "denso" not in cache:
        cache["denso"] = BuscaDensa(trechos)
    if nome == "denso":
        return cache["denso"]
    hibrida = BuscaHibrida(trechos, cache["bm25"], cache["denso"])
    if nome == "hibrido":
        return hibrida
    if nome == "hibridoRerank":
        return BuscaComRerank(hibrida)
    if nome == "densoRerank":
        return BuscaComRerank(cache["denso"])
    raise ValueError(f"Buscador desconhecido: {nome}")
