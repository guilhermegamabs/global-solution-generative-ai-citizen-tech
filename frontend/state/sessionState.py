import streamlit as st

chavesDaSessao = (
    "token",
    "emailUsuario",
    "registros",
    "idAtual",
    "buscaUpas",
    "etapaAuth",
    "emailPendente",
    "confirmarApagar",
    "conversa",
    "perguntaSugerida",
)


def iniciarEstado():
    st.session_state.setdefault("token", None)
    st.session_state.setdefault("emailUsuario", None)
    st.session_state.setdefault("registros", [])
    st.session_state.setdefault("idAtual", None)
    st.session_state.setdefault("buscaUpas", None)
    st.session_state.setdefault("etapaAuth", "entrar")
    st.session_state.setdefault("emailPendente", None)
    st.session_state.setdefault("conversa", [])
    st.session_state.setdefault("perguntaSugerida", None)


def obterConversa():
    return st.session_state["conversa"]


def adicionarMensagem(papel, texto, resposta=None):
    st.session_state["conversa"].append({"role": papel, "content": texto, "resposta": resposta})


def limparConversa():
    st.session_state["conversa"] = []


def definirPerguntaSugerida(pergunta):
    st.session_state["perguntaSugerida"] = pergunta


def consumirPerguntaSugerida():
    pergunta = st.session_state["perguntaSugerida"]
    st.session_state["perguntaSugerida"] = None
    return pergunta


def estaLogado():
    return st.session_state["token"] is not None


def obterToken():
    return st.session_state["token"]


def obterEmailUsuario():
    return st.session_state["emailUsuario"]


def definirSessao(token, email, registros):
    st.session_state["token"] = token
    st.session_state["emailUsuario"] = email
    st.session_state["registros"] = list(registros)
    st.session_state["idAtual"] = None
    st.session_state["etapaAuth"] = "entrar"
    st.session_state["emailPendente"] = None


def encerrarSessao():
    for chave in chavesDaSessao:
        st.session_state.pop(chave, None)
    iniciarEstado()


def obterEtapaAuth():
    return st.session_state["etapaAuth"]


def obterEmailPendente():
    return st.session_state["emailPendente"]


def definirEtapaAuth(etapa, emailPendente=None):
    st.session_state["etapaAuth"] = etapa
    st.session_state["emailPendente"] = emailPendente


def definirBuscaUpas(resultado):
    st.session_state["buscaUpas"] = resultado


def obterBuscaUpas():
    return st.session_state["buscaUpas"]


def obterRegistros():
    return st.session_state["registros"]


def adicionarRegistro(registro):
    st.session_state["registros"].insert(0, {**registro, "review": None})
    st.session_state["idAtual"] = registro["recordId"]


def obterRegistroAtual():
    idAtual = st.session_state["idAtual"]
    for registro in st.session_state["registros"]:
        if registro["recordId"] == idAtual:
            return registro
    return None


def aplicarRevisao(idRegistro, revisao):
    for registro in st.session_state["registros"]:
        if registro["recordId"] == idRegistro:
            registro["review"] = revisao


def limparAtual():
    st.session_state["idAtual"] = None
