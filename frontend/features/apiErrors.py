import streamlit as st

from providers.apiClient import SessaoExpiradaError
from state.sessionState import encerrarSessao
from ui.components import renderizarFaixaErro


def mostrarErroApi(erro):
    if isinstance(erro, SessaoExpiradaError):
        encerrarSessao()
        st.rerun()
    renderizarFaixaErro(str(erro))
