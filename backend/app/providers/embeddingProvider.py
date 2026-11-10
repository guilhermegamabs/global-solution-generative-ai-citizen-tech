import hashlib
import os
from functools import lru_cache
from pathlib import Path

import numpy as np

pastaCache = Path(__file__).resolve().parent.parent.parent / "knowledge" / "indice"


def obterNomeModeloEmbedding():
    return os.getenv("EMBEDDINGMODEL", "intfloat/multilingual-e5-small")


def obterNomeModeloReranker():
    return os.getenv("RERANKERMODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")


@lru_cache(maxsize=2)
def carregarModeloEmbedding(nome):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(nome, device="cpu")


@lru_cache(maxsize=2)
def carregarReranker(nome):
    from sentence_transformers import CrossEncoder

    return CrossEncoder(nome, device="cpu")


def codificarPassagens(textos, nomeModelo=None):
    nome = nomeModelo or obterNomeModeloEmbedding()
    assinatura = hashlib.sha256(("\x1e".join(textos) + nome).encode("utf-8")).hexdigest()[:16]
    arquivo = pastaCache / f"{assinatura}.npy"
    if arquivo.exists():
        return np.load(arquivo)
    modelo = carregarModeloEmbedding(nome)
    vetores = modelo.encode(
        [f"passage: {texto}" for texto in textos],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)
    pastaCache.mkdir(parents=True, exist_ok=True)
    np.save(arquivo, vetores)
    return vetores


def codificarConsulta(texto, nomeModelo=None):
    modelo = carregarModeloEmbedding(nomeModelo or obterNomeModeloEmbedding())
    return modelo.encode([f"query: {texto}"], normalize_embeddings=True, show_progress_bar=False)[0].astype(np.float32)


def pontuarPares(consulta, textos, nomeModelo=None):
    if not textos:
        return np.array([])
    modelo = carregarReranker(nomeModelo or obterNomeModeloReranker())
    return np.asarray(modelo.predict([(consulta, texto) for texto in textos], show_progress_bar=False))
