from pathlib import Path

import streamlit as st

from features.aboutScreen import renderizarSobre
from features.assistantScreen import renderizarAssistente
from features.authScreen import renderizarAutenticacao
from features.dashboardScreen import renderizarPainel
from features.historyScreen import renderizarHistorico
from features.sidebarPanel import renderizarBarraLateral
from features.triageScreen import renderizarTriagem
from features.unitsScreen import renderizarUpas
from state.sessionState import estaLogado, iniciarEstado
from ui.theme import aplicarTema

caminhoIcone = Path(__file__).parent / "assets" / "icone.png"

st.set_page_config(page_title="Orienta Saúde", page_icon=caminhoIcone, layout="wide")

iniciarEstado()
aplicarTema()
renderizarBarraLateral()

st.markdown(
    '<div class="appHeader"><h1>✚ Orienta Saúde</h1>'
    "<p>Descubra onde buscar atendimento, em linguagem simples.</p></div>",
    unsafe_allow_html=True,
)

if not estaLogado():
    renderizarAutenticacao()
    st.stop()

abaAssistente, abaTriagem, abaUpas, abaHistorico, abaPainel, abaSobre = st.tabs(
    ["💬 Assistente", "🩺 Triagem", "🗺️ UPAs próximas", "🗂️ Histórico", "📊 Painel", "ℹ️ Sobre"]
)

with abaAssistente:
    renderizarAssistente()
with abaTriagem:
    renderizarTriagem()
with abaUpas:
    renderizarUpas()
with abaHistorico:
    renderizarHistorico()
with abaPainel:
    renderizarPainel()
with abaSobre:
    renderizarSobre()
