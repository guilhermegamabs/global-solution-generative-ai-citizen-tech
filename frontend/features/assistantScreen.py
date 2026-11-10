import streamlit as st

from features.apiErrors import mostrarErroApi
from providers.apiClient import ApiError, buscarTemasAssistente, perguntarAssistente
from state.sessionState import (
    adicionarMensagem,
    consumirPerguntaSugerida,
    definirPerguntaSugerida,
    limparConversa,
    obterConversa,
    obterToken,
)
from ui.components import (
    renderizarCartaoFonte,
    renderizarEstadoVazio,
    renderizarFaixaEmergencia,
    renderizarSeloConfianca,
)
from ui.theme import rotulosTemas, significadosConfianca

turnosEnviados = 6

exemplos = [
    "A ligação para o SAMU é paga?",
    "Quais são os sinais de alarme da dengue?",
    "O que preciso levar para pegar remédio na Farmácia Popular?",
]

rotulosAlertas = {
    "personalDataRemoved": "Tiramos da pergunta dados pessoais (CPF, telefone, e-mail ou CEP) antes de enviar à IA.",
    "manipulationAttempt": "A mensagem parecia tentar mudar as regras do assistente e não foi enviada à IA.",
    "lowRetrievalScore": "Nenhuma fonte oficial tratava bem da pergunta, então a IA não foi chamada.",
    "suspiciousSourceLineRemoved": "Uma linha de fonte com texto suspeito foi removida antes de ir para a IA.",
    "promptLeakBlocked": "A resposta repetia instruções internas e foi bloqueada.",
    "noValidCitation": "A IA respondeu sem citar fonte válida, então a resposta foi descartada.",
    "unsupportedDoseBlocked": "A resposta citava dose de remédio que não está nas fontes e foi descartada.",
    "lowSupport": "A resposta usava palavras que não aparecem nas fontes, então foi descartada.",
}


def renderizarResposta(resposta):
    if resposta.get("emergencyNotice"):
        renderizarFaixaEmergencia(resposta["emergencyNotice"])
    st.markdown(resposta["answer"])
    renderizarSeloConfianca(resposta["confidence"])
    st.caption(significadosConfianca[resposta["confidence"]])

    if resposta["sources"]:
        with st.expander(f"📚 Fontes usadas ({len(resposta['sources'])})"):
            for fonte in resposta["sources"]:
                renderizarCartaoFonte(fonte)

    with st.expander("🔎 Como esta resposta foi feita"):
        diagnostico = resposta["diagnostics"]
        for alerta in resposta["alerts"]:
            st.markdown(f"- {rotulosAlertas.get(alerta, alerta)}")
        suporte = diagnostico["support"]
        st.markdown(
            f"- Busca usada: *{diagnostico['searchQuery']}*\n"
            f"- Recuperação: `{diagnostico['retriever']}` sobre trechos `{diagnostico['chunking']}`\n"
            f"- Relevância do melhor trecho: {diagnostico['topScore']:.2f} (0 a 1)\n"
            f"- Sustentação da resposta nas fontes: {'-' if suporte is None else f'{suporte:.0%}'}\n"
            f"- Modelo: `{diagnostico['model']}` · tempo: {diagnostico['latencyMs'] / 1000:.1f} s"
        )
    st.caption(resposta["disclaimer"])


avatares = {"user": ":material/person:", "assistant": ":material/medical_services:"}


def renderizarHistorico():
    for mensagem in obterConversa():
        with st.chat_message(mensagem["role"], avatar=avatares[mensagem["role"]]):
            if mensagem["resposta"]:
                renderizarResposta(mensagem["resposta"])
            else:
                st.markdown(mensagem["content"])


def montarCarga(pergunta, tema):
    historico = [
        {"role": mensagem["role"], "content": mensagem["content"]} for mensagem in obterConversa()[-turnosEnviados:]
    ]
    return {"question": pergunta, "history": historico, "topic": tema}


def enviarPergunta(pergunta, tema):
    carga = montarCarga(pergunta, tema)
    with st.chat_message("user", avatar=avatares["user"]):
        st.markdown(pergunta)
    with st.chat_message("assistant", avatar=avatares["assistant"]):
        try:
            with st.spinner("Procurando nas fontes do Ministério da Saúde..."):
                resposta = perguntarAssistente(carga, obterToken())
        except ApiError as erro:
            mostrarErroApi(erro)
            return
    adicionarMensagem("user", pergunta)
    adicionarMensagem("assistant", resposta["answer"], resposta)
    st.rerun()


def renderizarSeletorTema():
    try:
        temas = buscarTemasAssistente()
    except ApiError:
        temas = []
    opcoes = [None] + temas
    return st.selectbox(
        "Assunto (opcional)",
        opcoes,
        format_func=lambda tema: "Todos os assuntos" if tema is None else rotulosTemas.get(tema, tema),
        help="Escolher um assunto limita a busca às páginas desse tema.",
    )


def renderizarExemplos():
    renderizarEstadoVazio("💬", "Pergunte sobre saúde e serviços do SUS", "Ou comece por um destes exemplos:")
    colunas = st.columns(len(exemplos))
    for coluna, exemplo in zip(colunas, exemplos):
        if coluna.button(exemplo, width="stretch"):
            definirPerguntaSugerida(exemplo)
            st.rerun()


def renderizarAssistente():
    st.subheader("Assistente de dúvidas do SUS")
    st.caption(
        "🔒 Responde só com páginas oficiais do Ministério da Saúde e mostra de onde tirou cada informação. "
        "Não digite nome, CPF ou endereço. A conversa não é gravada. Em emergência, ligue 192."
    )

    colunaTema, colunaLimpar = st.columns([3, 1])
    with colunaTema:
        tema = renderizarSeletorTema()
    with colunaLimpar:
        st.write("")
        if st.button("Nova conversa", width="stretch"):
            limparConversa()
            st.rerun()

    pendente = consumirPerguntaSugerida()
    if not obterConversa() and not pendente:
        renderizarExemplos()
    renderizarHistorico()
    if pendente:
        enviarPergunta(pendente.strip(), tema)

    digitada = st.chat_input("Escreva sua dúvida sobre saúde ou SUS", max_chars=500)
    if digitada and digitada.strip():
        definirPerguntaSugerida(digitada)
        st.rerun()
