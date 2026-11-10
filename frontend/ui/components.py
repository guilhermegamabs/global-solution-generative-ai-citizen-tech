from html import escape
from urllib.parse import quote

import streamlit as st

from ui.theme import estilosConfianca, estilosUrgencia


def montarHtmlSelo(nivel, grande=False):
    estilo = estilosUrgencia[nivel]
    tamanho = " large" if grande else ""
    return (
        f'<span class="urgencyBadge{tamanho}" style="color:{estilo["cor"]};'
        f'background:{estilo["fundo"]};border-color:{estilo["borda"]}">'
        f'{estilo["icone"]} Urgência {estilo["rotulo"].lower()}</span>'
    )


def renderizarSeloUrgencia(nivel, grande=False):
    st.markdown(montarHtmlSelo(nivel, grande), unsafe_allow_html=True)


def renderizarCartaoMetrica(rotulo, valor, dica=""):
    st.markdown(
        f'<div class="metricCard"><div class="metricLabel">{escape(rotulo)}</div>'
        f'<div class="metricValue">{escape(str(valor))}</div>'
        f'<div class="metricHint">{escape(dica)}</div></div>',
        unsafe_allow_html=True,
    )


def renderizarCartaoInfo(titulo, itens, icone="•"):
    itensLista = "".join(f"<li>{escape(item)}</li>" for item in itens)
    st.markdown(
        f'<div class="infoCard"><h4>{escape(icone)} {escape(titulo)}</h4><ul>{itensLista}</ul></div>',
        unsafe_allow_html=True,
    )


def renderizarEstadoVazio(icone, titulo, mensagem):
    st.markdown(
        f'<div class="emptyState"><div class="emptyIcon" aria-hidden="true">{escape(icone)}</div>'
        f"<strong>{escape(titulo)}</strong><br>{escape(mensagem)}</div>",
        unsafe_allow_html=True,
    )


def renderizarCartaoProtocolo(protocolo):
    st.markdown(
        f'<div class="protocolCard"><span class="protocolLabel">Guarde este protocolo</span>'
        f'<span class="protocolCode">{escape(protocolo)}</span></div>',
        unsafe_allow_html=True,
    )


def renderizarAviso(texto):
    st.markdown(
        f'<div class="noticeCard">ℹ️ {escape(texto)}</div>',
        unsafe_allow_html=True,
    )


def renderizarCartaoConfirmacao(protocolo, nivel):
    st.markdown(
        f'<div class="confirmCard" role="status"><strong>✅ Resposta registrada</strong>'
        f'<div class="confirmLine">Protocolo {escape(protocolo)}</div>'
        f'<div class="confirmLine">{montarHtmlSelo(nivel)}</div></div>',
        unsafe_allow_html=True,
    )


def montarLinkRota(unidade, cidade):
    partes = [unidade["name"], unidade["address"], unidade["neighborhood"], cidade]
    destino = quote(", ".join(parte for parte in partes if parte))
    return f"https://www.google.com/maps/dir/?api=1&destination={destino}"


def renderizarCartaoUnidade(posicao, unidade, cidade=""):
    incerta = unidade.get("positionUncertain", False)
    distancia = f'{"cerca de " if incerta else ""}{unidade["distanceKm"]:.1f}'.replace(".", ",")
    avisoPosicao = (
        '<div class="unitMeta unitWarning">⚠️ Posição no mapa aproximada. Use o “Como chegar” para o endereço certo.</div>'
        if incerta
        else ""
    )
    horario = "🕒 Atendimento 24 horas" if unidade["open24h"] else "🕒 Confirme o horário por telefone"
    telefone = unidade.get("phone")
    linhaTelefone = ""
    if telefone:
        numeros = "".join(caractere for caractere in telefone if caractere.isdigit() or caractere == "+")
        linhaTelefone = f'<div class="unitMeta">📞 <a href="tel:{escape(numeros)}">{escape(telefone)}</a></div>'
    rota = montarLinkRota(unidade, cidade)
    bairro = f' — {escape(unidade["neighborhood"])}' if unidade["neighborhood"] else ""
    st.markdown(
        f'<div class="unitCard"><div class="unitNumber" aria-hidden="true">{posicao}</div><div>'
        f'<div class="unitName">{escape(unidade["name"])}</div>'
        f'<div class="unitMeta">📍 {escape(unidade["address"])}{bairro}</div>'
        f'<div class="unitMeta">🧭 A {distancia} km de você · {horario}</div>'
        f"{avisoPosicao}"
        f"{linhaTelefone}"
        f'<div class="unitMeta"><a href="{rota}" target="_blank" rel="noopener noreferrer">Como chegar ↗</a></div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def renderizarSeloConfianca(nivel):
    estilo = estilosConfianca[nivel]
    st.markdown(
        f'<span class="urgencyBadge" style="color:{estilo["cor"]};'
        f'background:{estilo["fundo"]};border-color:{estilo["borda"]}">'
        f'{estilo["icone"]} {estilo["rotulo"]}</span>',
        unsafe_allow_html=True,
    )


def renderizarCartaoFonte(fonte):
    secao = f' — {escape(fonte["section"])}' if fonte["section"] else ""
    st.markdown(
        f'<div class="sourceCard"><div class="sourceTitle">[{fonte["number"]}] {escape(fonte["title"])}{secao}</div>'
        f'<div class="sourceMeta">Ministério da Saúde · consultado em {escape(fonte["accessedAt"])} · '
        f'<a href="{escape(fonte["url"])}" target="_blank" rel="noopener noreferrer">abrir página ↗</a></div>'
        f'<div class="sourceExcerpt">{escape(fonte["excerpt"])}…</div></div>',
        unsafe_allow_html=True,
    )


def renderizarFaixaEmergencia(mensagem):
    st.markdown(
        f'<div class="alertBanner" role="alert">🚨 {escape(mensagem)}</div>',
        unsafe_allow_html=True,
    )


def renderizarFaixaErro(mensagem, icone="⚠️"):
    st.error(mensagem, icon=icone)
