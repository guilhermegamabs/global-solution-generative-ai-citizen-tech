import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

pastaFontes = Path("C:/Windows/Fonts")
for nome, arquivo in [("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf"), ("Arial-Italic", "ariali.ttf"), ("Arial-BoldItalic", "arialbi.ttf"), ("Mono", "consola.ttf")]:
    pdfmetrics.registerFont(TTFont(nome, str(pastaFontes / arquivo)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic")

pasta = Path(__file__).parent
origem = pasta / "relatorioAvaliacao.md"
destino = pasta / "relatorioAvaliacao.pdf"

disciplina = "Generative AI & Advanced Nets"
tituloProjeto = "CitizenTech · Orienta Saúde"
subtitulo = "Assistente conversacional com RAG: avaliação de chunking, recuperação, geração e segurança"
repositorio = "https://github.com/guilhermegamabs/global-solution-generative-ai-citizen-tech"
rodapeTexto = f"CitizenTech 2026.2  |  Global Solution  |  {disciplina}"

preto = colors.HexColor("#111111")
cinza = colors.HexColor("#555555")
linha = colors.HexColor("#999999")
zebra = colors.HexColor("#F3F3F3")

corpo = ParagraphStyle("corpo", fontName="Arial", fontSize=9.5, leading=13, textColor=preto, spaceAfter=5)
secao = ParagraphStyle("secao", parent=corpo, fontName="Arial-Bold", fontSize=13, leading=16, spaceBefore=12, spaceAfter=5, keepWithNext=1)
subsecao = ParagraphStyle("subsecao", parent=corpo, fontName="Arial-Bold", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3, keepWithNext=1)
subsubsecao = ParagraphStyle("subsubsecao", parent=subsecao, fontSize=9.5, leading=13)
marcador = ParagraphStyle("marcador", parent=corpo, leftIndent=14, bulletIndent=3, spaceAfter=2)
marcadorInterno = ParagraphStyle("marcadorInterno", parent=marcador, leftIndent=28, bulletIndent=17)
tituloPagina = ParagraphStyle("tituloPagina", parent=corpo, fontName="Arial-Bold", fontSize=17, leading=21, spaceAfter=3)
subtituloPagina = ParagraphStyle("subtituloPagina", parent=corpo, fontSize=9.5, leading=13, textColor=cinza, spaceAfter=6)
capaInstituicao = ParagraphStyle("capaInstituicao", parent=corpo, fontName="Arial-Bold", fontSize=15, leading=19, alignment=TA_CENTER, spaceAfter=2)
capaTexto = ParagraphStyle("capaTexto", parent=corpo, fontSize=9.5, leading=13, alignment=TA_CENTER, spaceAfter=0)
capaDisciplina = ParagraphStyle("capaDisciplina", parent=corpo, fontSize=11.5, leading=15, alignment=TA_CENTER, spaceAfter=0)
capaTitulo = ParagraphStyle("capaTitulo", parent=corpo, fontName="Arial-Bold", fontSize=22, leading=27, alignment=TA_CENTER, spaceAfter=6)
capaSubtitulo = ParagraphStyle("capaSubtitulo", parent=corpo, fontSize=11, leading=15, alignment=TA_CENTER, textColor=preto)
capaRotulo = ParagraphStyle("capaRotulo", parent=corpo, fontName="Arial-Bold", fontSize=9, leading=12, spaceAfter=0)
capaValor = ParagraphStyle("capaValor", parent=corpo, fontSize=9, leading=12, spaceAfter=0)


def escapar(texto):
    return texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def formatarTrecho(texto):
    texto = escapar(texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", texto)
    return texto


def formatarInline(texto):
    texto = re.sub(r"\[([^\]]+)\]\((?!http)[^)]+\)", r"\1", texto)
    texto = texto.replace("\\*", "\u0001")
    partes = re.split(r"(`[^`]+`)", texto)
    saida = []
    for parte in partes:
        if len(parte) > 1 and parte.startswith("`") and parte.endswith("`"):
            saida.append(f'<font name="Mono" size="8.5">{escapar(parte[1:-1])}</font>')
        else:
            saida.append(formatarTrecho(parte))
    return "".join(saida).replace("\u0001", "*")


def dividirLinhaTabela(texto):
    return [celula.strip() for celula in texto.strip().strip("|").split("|")]


def montarTabela(linhas):
    cabecalho = dividirLinhaTabela(linhas[0])
    corpoLinhas = [dividirLinhaTabela(l) for l in linhas[2:]]
    colunas = len(cabecalho)
    tamanho = 8.5 if colunas <= 4 else 7.5 if colunas <= 6 else 6.5
    estiloCelula = ParagraphStyle("celula", parent=corpo, fontSize=tamanho, leading=tamanho + 3, spaceAfter=0)
    estiloCabecalho = ParagraphStyle("cabecalho", parent=estiloCelula, fontName="Arial-Bold", textColor=colors.white)
    dados = [[Paragraph(formatarInline(c), estiloCabecalho) for c in cabecalho]]
    for l in corpoLinhas:
        l = (l + [""] * colunas)[:colunas]
        dados.append([Paragraph(formatarInline(c), estiloCelula) for c in l])
    pesos = []
    for indice in range(colunas):
        textos = [cabecalho[indice]] + [l[indice] if indice < len(l) else "" for l in corpoLinhas]
        media = sum(len(t) for t in textos) / len(textos)
        maiorPalavra = max(len(p) for t in textos for p in (t.split() or [""]))
        pesos.append(max(11, min(45, media), min(maiorPalavra + 2, 14)))
    largura = A4[0] - 4 * cm
    total = sum(pesos)
    larguras = [largura * p / total for p in pesos]
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), preto),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, zebra]),
                ("GRID", (0, 0), (-1, -1), 0.4, linha),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return [tabela, Spacer(1, 7)]


def converterMarkdown(texto):
    linhas = texto.splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("## "))
    linhas = linhas[inicio:]
    elementos = []
    paragrafo = []
    indice = 0

    def fecharParagrafo():
        if paragrafo:
            elementos.append(Paragraph(formatarInline(" ".join(paragrafo)), corpo))
            paragrafo.clear()

    while indice < len(linhas):
        atual = linhas[indice]
        if atual.startswith("|"):
            fecharParagrafo()
            bloco = []
            while indice < len(linhas) and linhas[indice].startswith("|"):
                bloco.append(linhas[indice])
                indice += 1
            elementos.extend(montarTabela(bloco))
            continue
        cabecalho = re.match(r"^(#{2,4}) (.+)$", atual)
        item = re.match(r"^(\s*)- (.+)$", atual)
        numerado = re.match(r"^(\d+)\. (.+)$", atual)
        if cabecalho:
            fecharParagrafo()
            nivel = len(cabecalho.group(1))
            estilo = {2: secao, 3: subsecao, 4: subsubsecao}[nivel]
            elementos.append(Paragraph(formatarInline(cabecalho.group(2)), estilo))
        elif item:
            fecharParagrafo()
            interno = len(item.group(1)) >= 2
            elementos.append(Paragraph(formatarInline(item.group(2)), marcadorInterno if interno else marcador, bulletText="•" if not interno else "–"))
        elif numerado:
            fecharParagrafo()
            elementos.append(Paragraph(formatarInline(numerado.group(2)), marcador, bulletText=f"{numerado.group(1)}."))
        elif not atual.strip():
            fecharParagrafo()
        else:
            paragrafo.append(atual.strip())
        indice += 1
    fecharParagrafo()
    return elementos


def capa():
    metadados = [
        ["Disciplina", disciplina],
        ["Turma", "2TIAPF-2026"],
        ["Ano / semestre", "2026 · 2º semestre (Global Solution 2026.2)"],
        ["Integrante", "Guilherme Gama Bitencourt Souza · RM565293"],
        ["Repositório", repositorio],
    ]
    dados = [[Paragraph(r, capaRotulo), Paragraph(v, capaValor)] for r, v in metadados]
    tabela = Table(dados, colWidths=[3.6 * cm, 12.4 * cm])
    tabela.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, linha),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        Spacer(1, 1.8 * cm),
        Paragraph("FIAP", capaInstituicao),
        Paragraph("Faculdade de Informática e Administração Paulista", capaTexto),
        Paragraph("Tecnologia em Inteligência Artificial", capaTexto),
        Spacer(1, 0.5 * cm),
        HRFlowable(width="100%", thickness=1, color=preto),
        Spacer(1, 3 * cm),
        Paragraph("GLOBAL SOLUTION 2026.2", capaTexto),
        Spacer(1, 0.2 * cm),
        Paragraph(disciplina, capaDisciplina),
        Spacer(1, 1.6 * cm),
        Paragraph(tituloProjeto, capaTitulo),
        Paragraph(subtitulo, capaSubtitulo),
        Spacer(1, 2.4 * cm),
        tabela,
        Spacer(1, 2.4 * cm),
        Paragraph("São Paulo · novembro de 2026", capaTexto),
        NextPageTemplate("conteudo"),
        PageBreak(),
    ]


def rodape(canvas, documento):
    canvas.saveState()
    canvas.setFont("Arial", 7.5)
    canvas.setFillColor(cinza)
    canvas.drawString(2 * cm, 1.2 * cm, rodapeTexto)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {documento.page - 1}")
    canvas.restoreState()


def gerar():
    documento = BaseDocTemplate(
        str(destino),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title=f"{tituloProjeto} — Relatório de avaliação do assistente RAG",
        author="Guilherme Gama Bitencourt Souza",
        subject=f"Global Solution 2026.2 — {disciplina}",
    )
    quadro = Frame(documento.leftMargin, documento.bottomMargin, documento.width, documento.height, id="quadro")
    documento.addPageTemplates(
        [
            PageTemplate(id="capa", frames=[quadro]),
            PageTemplate(id="conteudo", frames=[quadro], onPage=rodape),
        ]
    )
    cabecalhoPagina = [Paragraph(tituloProjeto, tituloPagina), Paragraph(f"{subtitulo} · Global Solution 2026.2 · {disciplina} · Tecnologia em Inteligência Artificial (FIAP)", subtituloPagina)]
    elementos = capa() + cabecalhoPagina + converterMarkdown(origem.read_text(encoding="utf-8"))
    documento.build(elementos)


if __name__ == "__main__":
    gerar()
