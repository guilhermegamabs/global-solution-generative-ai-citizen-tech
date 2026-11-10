import streamlit as st

from features.triageForm import renderizarFormularioTriagem, validarEntrada
from features.triageResult import renderizarResultado
from providers.apiClient import ApiError, buscarOpcoes, solicitarTriagem
from features.apiErrors import mostrarErroApi
from state.sessionState import adicionarRegistro, obterRegistroAtual, obterToken
from ui.components import renderizarEstadoVazio, renderizarFaixaErro


def processarEnvio(envio):
    problemas = validarEntrada(envio)
    if problemas:
        for problema in problemas:
            st.warning(problema, icon="✏️")
        return

    try:
        with st.spinner("Analisando seus sintomas. Isso leva alguns segundos..."):
            registro = solicitarTriagem(envio["carga"], obterToken())
    except ApiError as erro:
        mostrarErroApi(erro)
        return

    adicionarRegistro(registro)
    st.toast("Orientação pronta. Veja o resultado abaixo do formulário ou na coluna ao lado.")


def renderizarTriagem():
    try:
        opcoes = buscarOpcoes()
    except ApiError as erro:
        renderizarFaixaErro(str(erro))
        st.button("Tentar novamente")
        return

    colunaFormulario, colunaResultado = st.columns(2, gap="large")

    with colunaFormulario:
        st.subheader("1. Conte o que está acontecendo")
        envio = renderizarFormularioTriagem(opcoes)
        if envio:
            processarEnvio(envio)

    with colunaResultado:
        st.subheader("2. Veja a orientação")
        registro = obterRegistroAtual()
        if registro:
            renderizarResultado(registro)
        else:
            renderizarEstadoVazio(
                "🩺",
                "Nenhuma análise ainda",
                "Preencha o formulário ao lado e clique em Analisar sintomas.",
            )
