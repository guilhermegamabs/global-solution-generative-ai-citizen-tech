import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

pastaConhecimento = Path(__file__).resolve().parent.parent / "knowledge"
arquivoFontes = pastaConhecimento / "fontes.json"
arquivoCorpus = pastaConhecimento / "corpus.json"
arquivoTabela = pastaConhecimento / "FONTES.md"

agenteUsuario = "Mozilla/5.0 (OrientaSaudeRAG; projeto academico FIAP)"
blocosDeTexto = ["h1", "h2", "h3", "h4", "p", "li", "td"]
seletoresRuido = [
    "script",
    "style",
    "nav",
    "form",
    "#viewlet-above-content",
    "#viewlet-below-content",
    ".documentActions",
    ".documentByLine",
    ".social-links",
    ".share",
    ".portalMessage",
    "#plone-document-byline",
]
linhasDescartadas = re.compile(
    r"^(compartilhe|link para a página|copiar para área de transferência|publicado em|atualizado em|foto:|notícias$)", re.I
)


def limparEspacos(texto):
    return re.sub(r"\s+", " ", texto.replace("\xa0", " ")).strip()


def contemOutroBloco(elemento):
    return elemento.find(blocosDeTexto) is not None


def dentroDeOutroBloco(elemento, raiz):
    pai = elemento.parent
    while pai is not None and pai is not raiz:
        if pai.name in blocosDeTexto and not contemOutroBloco(pai):
            return True
        pai = pai.parent
    return False


def extrairData(sopa, classe):
    alvo = sopa.select_one(f".{classe} .value") or sopa.select_one(f".{classe}")
    if not alvo:
        return None
    achado = re.search(r"\d{2}/\d{2}/\d{4}", alvo.get_text(" "))
    return achado.group(0) if achado else None


def extrairMarkdown(html):
    sopa = BeautifulSoup(html, "html.parser")
    titulo = limparEspacos(sopa.select_one("h1.documentFirstHeading").get_text()) if sopa.select_one("h1.documentFirstHeading") else limparEspacos(sopa.title.get_text().split("—")[0])
    publicadoEm = extrairData(sopa, "documentPublished")
    atualizadoEm = extrairData(sopa, "documentModified")
    conteudo = sopa.select_one("#content") or sopa.select_one("main")
    for seletor in seletoresRuido:
        for ruido in conteudo.select(seletor):
            ruido.decompose()
    for pergunta in conteudo.select("a.toggle"):
        pergunta.name = "h3"

    linhas = []
    for elemento in conteudo.find_all(blocosDeTexto):
        if contemOutroBloco(elemento) or dentroDeOutroBloco(elemento, conteudo):
            continue
        texto = limparEspacos(elemento.get_text(" "))
        if len(texto) < 3 or linhasDescartadas.match(texto):
            continue
        if elemento.name in ("h1", "h2"):
            linhas.append(f"## {texto}")
        elif elemento.name in ("h3", "h4"):
            linhas.append(f"### {texto}")
        elif elemento.name == "li":
            linhas.append(f"- {texto}")
        else:
            linhas.append(texto)

    semRepeticao = []
    for linha in linhas:
        if not semRepeticao or semRepeticao[-1] != linha:
            semRepeticao.append(linha)
    if semRepeticao and semRepeticao[0].lstrip("# ").strip() == titulo:
        semRepeticao = semRepeticao[1:]
    return titulo, publicadoEm, atualizadoEm, "\n".join(semRepeticao)


def coletar():
    fontes = json.loads(arquivoFontes.read_text(encoding="utf-8"))
    documentos = []
    falhas = []
    with httpx.Client(headers={"User-Agent": agenteUsuario}, follow_redirects=True, timeout=40) as cliente:
        for fonte in fontes:
            try:
                resposta = cliente.get(fonte["url"])
                resposta.raise_for_status()
            except httpx.HTTPError as erro:
                falhas.append((fonte["docId"], str(erro)))
                continue
            titulo, publicadoEm, atualizadoEm, texto = extrairMarkdown(resposta.text)
            documentos.append(
                {
                    **fonte,
                    "titulo": titulo,
                    "publicadoEm": publicadoEm,
                    "atualizadoEm": atualizadoEm,
                    "acessadoEm": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "texto": texto,
                }
            )
            print(f"ok {fonte['docId']}: {len(texto)} caracteres")
            time.sleep(0.5)

    arquivoCorpus.write_text(json.dumps(documentos, ensure_ascii=False, indent=1), encoding="utf-8")
    escreverTabela(documentos)
    for docId, erro in falhas:
        print(f"falhou {docId}: {erro}", file=sys.stderr)
    print(f"{len(documentos)} documentos salvos em {arquivoCorpus}")


def escreverTabela(documentos):
    linhas = [
        "# Fontes do corpus",
        "",
        "Gerado por `python -m scripts.coletarCorpus`. Todas as páginas são do portal gov.br do Ministério da Saúde.",
        "",
        "| docId | Tema | Título | Atualizado na fonte | Consultado em | Caracteres | URL |",
        "|---|---|---|---|---|---|---|",
    ]
    for documento in documentos:
        linhas.append(
            f"| {documento['docId']} | {documento['tema']} | {documento['titulo']} | "
            f"{documento['atualizadoEm'] or documento['publicadoEm'] or '-'} | {documento['acessadoEm']} | "
            f"{len(documento['texto'])} | {documento['url']} |"
        )
    arquivoTabela.write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    coletar()
