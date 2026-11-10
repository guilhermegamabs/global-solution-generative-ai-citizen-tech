import streamlit as st

from features.apiErrors import mostrarErroApi
from providers.apiClient import ApiError, apagarConta, sairDaConta
from state.sessionState import encerrarSessao, estaLogado, obterEmailUsuario, obterRegistros, obterToken
from ui.components import renderizarCartaoInfo


def sairAgora():
    try:
        sairDaConta(obterToken())
    except ApiError:
        pass
    encerrarSessao()
    st.rerun()


def apagarAgora():
    try:
        apagarConta(obterToken())
    except ApiError as erro:
        mostrarErroApi(erro)
        return
    encerrarSessao()
    st.rerun()


def renderizarMinhaConta():
    st.caption(f"👤 {obterEmailUsuario()}")
    if st.button("Sair da conta", width="stretch"):
        sairAgora()

    with st.expander("Apagar minha conta"):
        st.caption("Apaga seu e-mail e todo o seu histórico. Não dá para desfazer.")
        confirmou = st.checkbox("Quero apagar tudo", key="confirmarApagar")
        if st.button("Apagar definitivamente", disabled=not confirmou):
            apagarAgora()


def renderizarBarraLateral():
    with st.sidebar:
        st.markdown("## ✚ Orienta Saúde")
        renderizarCartaoInfo(
            "Telefones de emergência",
            ["SAMU: 192", "Bombeiros: 193", "Disque Saúde: 136"],
            "📞",
        )
        if estaLogado():
            st.caption(f"Análises no seu histórico: {len(obterRegistros())}")
            renderizarMinhaConta()
        st.caption("Em caso de dúvida ou piora, procure atendimento presencial.")
