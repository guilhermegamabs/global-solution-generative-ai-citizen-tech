import streamlit as st

from state.recordFrame import resolverUrgencia
from state.sessionState import obterRegistros
from ui.components import renderizarCartaoInfo, renderizarEstadoVazio, renderizarSeloUrgencia
from ui.theme import estilosUrgencia, rotulosDecisao, rotulosServico


def formatarData(dataIso):
    return dataIso[:16].replace("T", " ")


def renderizarHistorico():
    st.subheader("Seu histórico")
    registros = obterRegistros()

    if not registros:
        renderizarEstadoVazio("🗂️", "Histórico vazio", "Quando você fizer uma análise, ela aparece aqui.")
        return

    for registro in registros:
        nivel = resolverUrgencia(registro)
        estilo = estilosUrgencia[nivel]
        titulo = f'{estilo["icone"]} {formatarData(registro["createdAt"])} — {registro["protocol"]} — {estilo["rotulo"]}'
        with st.expander(titulo):
            renderizarSeloUrgencia(nivel)
            st.write(registro["summary"])
            renderizarCartaoInfo("Onde procurar atendimento", [rotulosServico[registro["recommendedService"]]], "📍")
            renderizarCartaoInfo("O que fazer", registro["guidance"], "📝")
            revisao = registro["review"]
            situacao = rotulosDecisao[revisao["decision"]] if revisao else rotulosDecisao["pending"]
            st.caption(f"Revisão: {situacao}")
