import json
import os
from functools import lru_cache
from pathlib import Path

from app.rag.chunking import ConfiguracaoChunking, gerarTrechos
from app.rag.retrieval import construirBuscador

arquivoCorpus = Path(__file__).resolve().parent.parent.parent / "knowledge" / "corpus.json"

configuracaoPadrao = ConfiguracaoChunking(estrategia="estrutural", tamanho=1200, sobreposicao=200)
buscadorPadrao = "densoRerank"


def carregarDocumentos(caminho=arquivoCorpus):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


class BaseConhecimento:
    def __init__(self, documentos, configuracao=configuracaoPadrao, nomeBuscador=buscadorPadrao):
        self.documentos = documentos
        self.configuracao = configuracao
        self.trechos = gerarTrechos(documentos, configuracao)
        self.cacheBuscadores = {}
        self.buscador = construirBuscador(nomeBuscador, self.trechos, self.cacheBuscadores)
        self.temas = sorted({documento["tema"] for documento in documentos})

    def trocarBuscador(self, nomeBuscador):
        self.buscador = construirBuscador(nomeBuscador, self.trechos, self.cacheBuscadores)
        return self

    def posicoesDoTema(self, tema):
        if not tema:
            return None
        return {posicao for posicao, trecho in enumerate(self.trechos) if trecho.tema == tema}

    def buscar(self, consulta, k=5, tema=None):
        return self.buscador.buscar(consulta, k, self.posicoesDoTema(tema))


def obterConfiguracaoAmbiente():
    return ConfiguracaoChunking(
        estrategia=os.getenv("CHUNKESTRATEGIA", configuracaoPadrao.estrategia),
        tamanho=int(os.getenv("CHUNKTAMANHO", configuracaoPadrao.tamanho)),
        sobreposicao=int(os.getenv("CHUNKSOBREPOSICAO", configuracaoPadrao.sobreposicao)),
    )


def aquecerRag():
    obterBaseConhecimento().buscar("Quando devo ligar para o SAMU?", 1)


@lru_cache(maxsize=1)
def obterBaseConhecimento():
    return BaseConhecimento(
        carregarDocumentos(),
        obterConfiguracaoAmbiente(),
        os.getenv("BUSCADOR", buscadorPadrao),
    )
