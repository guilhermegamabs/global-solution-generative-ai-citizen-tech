from dataclasses import dataclass

from app.rag.textUtils import dividirFrases


@dataclass(frozen=True)
class ConfiguracaoChunking:
    estrategia: str
    tamanho: int
    sobreposicao: int

    @property
    def chave(self):
        return f"{self.estrategia}-{self.tamanho}-{self.sobreposicao}"


@dataclass
class Trecho:
    chunkId: str
    docId: str
    titulo: str
    secao: str
    url: str
    tema: str
    acessadoEm: str
    texto: str

    @property
    def textoIndexado(self):
        cabecalho = f"{self.titulo} — {self.secao}" if self.secao else self.titulo
        return f"{cabecalho}\n{self.texto}"


def metadadosDe(documento):
    return {
        "docId": documento["docId"],
        "titulo": documento["titulo"],
        "url": documento["url"],
        "tema": documento["tema"],
        "acessadoEm": documento["acessadoEm"],
    }


def ajustarAoEspaco(texto, inicio, fim):
    if fim >= len(texto):
        return len(texto)
    espaco = texto.rfind(" ", inicio, fim)
    return espaco if espaco > inicio else fim


def chunkingTamanhoFixo(documento, configuracao):
    texto = documento["texto"].replace("\n", " ")
    passo = max(1, configuracao.tamanho - configuracao.sobreposicao)
    trechos = []
    inicio = 0
    while inicio < len(texto):
        fim = ajustarAoEspaco(texto, inicio, inicio + configuracao.tamanho)
        pedaco = texto[inicio:fim].strip()
        if pedaco:
            trechos.append(
                Trecho(
                    chunkId=f"{documento['docId']}#{len(trechos)}",
                    secao="",
                    texto=pedaco,
                    **metadadosDe(documento),
                )
            )
        if fim >= len(texto):
            break
        proximo = ajustarAoEspaco(texto, inicio, inicio + passo)
        inicio = proximo + 1 if proximo > inicio else inicio + passo
    return trechos


def separarSecoes(texto):
    secoes = []
    caminho = []
    atual = []
    for linha in texto.split("\n"):
        if linha.startswith("#"):
            if atual:
                secoes.append((" > ".join(caminho), atual))
                atual = []
            nivel = len(linha) - len(linha.lstrip("#"))
            titulo = linha.lstrip("# ").strip()
            caminho = caminho[: max(0, nivel - 2)] + [titulo]
        else:
            atual.append(linha)
    if atual:
        secoes.append((" > ".join(caminho), atual))
    return secoes


def quebrarUnidadeLonga(unidade, tamanho):
    if len(unidade) <= tamanho:
        return [unidade]
    pedacos = []
    atual = ""
    for frase in dividirFrases(unidade):
        if atual and len(atual) + len(frase) + 1 > tamanho:
            pedacos.append(atual)
            atual = frase
        else:
            atual = f"{atual} {frase}".strip()
    if atual:
        pedacos.append(atual)
    return pedacos


def agruparUnidades(unidades, configuracao):
    blocos = []
    atual = []
    for unidade in unidades:
        tamanhoAtual = sum(len(item) + 1 for item in atual)
        if atual and tamanhoAtual + len(unidade) > configuracao.tamanho:
            blocos.append(atual)
            reaproveitadas = []
            for item in reversed(atual):
                if sum(len(x) + 1 for x in reaproveitadas) + len(item) > configuracao.sobreposicao:
                    break
                reaproveitadas.insert(0, item)
            atual = reaproveitadas
        atual.append(unidade)
    if atual:
        blocos.append(atual)
    return blocos


def chunkingEstrutural(documento, configuracao):
    trechos = []
    for secao, linhas in separarSecoes(documento["texto"]):
        unidades = []
        for linha in linhas:
            unidades.extend(quebrarUnidadeLonga(linha.strip(), configuracao.tamanho))
        unidades = [unidade for unidade in unidades if unidade]
        if not unidades:
            continue
        for bloco in agruparUnidades(unidades, configuracao):
            trechos.append(
                Trecho(
                    chunkId=f"{documento['docId']}#{len(trechos)}",
                    secao=secao,
                    texto="\n".join(bloco),
                    **metadadosDe(documento),
                )
            )
    return trechos


estrategias = {
    "tamanhoFixo": chunkingTamanhoFixo,
    "estrutural": chunkingEstrutural,
}


def gerarTrechos(documentos, configuracao):
    funcao = estrategias[configuracao.estrategia]
    trechos = []
    for documento in documentos:
        trechos.extend(funcao(documento, configuracao))
    return trechos
