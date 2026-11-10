import streamlit as st

from providers.apiClient import ApiError, enviarRevisao
from features.apiErrors import mostrarErroApi
from state.sessionState import aplicarRevisao, limparAtual, obterToken
from ui.components import (
    renderizarAviso,
    renderizarCartaoConfirmacao,
    renderizarCartaoInfo,
    renderizarCartaoProtocolo,
    renderizarFaixaEmergencia,
    renderizarSeloUrgencia,
)
from ui.theme import estilosUrgencia, ordemUrgencia, rotulosDecisao, rotulosServico, significadosUrgencia


def formatarUrgencia(nivel):
    estilo = estilosUrgencia[nivel]
    return f'{estilo["icone"]} {estilo["rotulo"]}'


def renderizarRevisao(registro):
    idRegistro = registro["recordId"]
    revisao = registro["review"]

    if revisao:
        renderizarCartaoConfirmacao(registro["protocol"], revisao["finalUrgency"])
        return

    st.markdown("#### Você confirma esta orientação?")
    st.caption(
        "Sua avaliação vale mais que a da IA. Confirmar ou corrigir não avisa nenhum médico nem a UPA: "
        "serve para registrar a sua opinião e melhorar o app."
    )

    decisao = st.radio(
        "Sua decisão",
        ["confirmed", "corrected"],
        format_func=rotulosDecisao.get,
        key=f"decision{idRegistro}",
    )

    urgenciaCorrigida = None
    if decisao == "corrected":
        urgenciaCorrigida = st.selectbox(
            "Qual urgência você considera correta?",
            ordemUrgencia,
            format_func=formatarUrgencia,
            key=f"corrected{idRegistro}",
        )

    util = st.radio(
        "A orientação foi útil?",
        [True, False],
        format_func=lambda valor: "Sim" if valor else "Não",
        horizontal=True,
        key=f"helpful{idRegistro}",
    )

    if st.button("Registrar minha resposta", type="primary", key=f"send{idRegistro}"):
        try:
            with st.spinner("Registrando..."):
                resposta = enviarRevisao(
                    {
                        "recordId": idRegistro,
                        "decision": decisao,
                        "correctedUrgency": urgenciaCorrigida,
                        "helpful": util,
                    },
                    obterToken(),
                )
        except ApiError as erro:
            mostrarErroApi(erro)
            return
        aplicarRevisao(idRegistro, {**resposta, "helpful": util})
        st.rerun()


def renderizarResultado(registro):
    if registro["urgencyLevel"] == "emergency":
        renderizarFaixaEmergencia("Ligue 192 (SAMU) agora ou vá ao pronto-socorro mais próximo.")

    renderizarSeloUrgencia(registro["urgencyLevel"], grande=True)
    st.caption(significadosUrgencia[registro["urgencyLevel"]])
    st.markdown(f'**{registro["summary"]}**')

    renderizarCartaoInfo("Onde procurar atendimento", [rotulosServico[registro["recommendedService"]]], "📍")
    if registro["recommendedService"] == "urgentCare":
        st.caption("🗺️ Veja as UPAs mais próximas na aba “UPAs próximas”.")
    renderizarCartaoInfo("O que fazer agora", registro["guidance"], "📝")
    renderizarCartaoInfo("Procure ajuda imediata se...", registro["warningSignsToWatch"], "⚠️")

    with st.expander("Por que a IA chegou a este resultado?"):
        st.write(registro["rationale"])

    renderizarAviso(registro["disclaimer"])
    st.divider()
    renderizarRevisao(registro)
    renderizarCartaoProtocolo(registro["protocol"])

    if st.button("Fazer nova análise", key=f'new{registro["recordId"]}', width="stretch"):
        limparAtual()
        st.rerun()
