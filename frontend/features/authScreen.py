import re

import streamlit as st

from providers.apiClient import (
    ApiError,
    buscarHistorico,
    cadastrarConta,
    entrarNaConta,
    reenviarCodigo,
    verificarCodigo,
)
from state.sessionState import definirEtapaAuth, definirSessao, obterEmailPendente, obterEtapaAuth
from ui.components import renderizarFaixaErro

padraoEmail = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
tamanhoMinimoSenha = 8


def iniciarSessaoComHistorico(resposta):
    try:
        registros = buscarHistorico(resposta["token"])
    except ApiError:
        registros = []
        st.warning("Entramos na sua conta, mas não conseguimos carregar o histórico agora.")
    definirSessao(resposta["token"], resposta["email"], registros)
    st.rerun()


def validarCredenciais(email, senha, confirmacao=None, consentimento=None):
    problemas = []
    if not padraoEmail.match(email):
        problemas.append("Digite um e-mail válido, por exemplo nome@exemplo.com.")
    if len(senha) < tamanhoMinimoSenha:
        problemas.append("A senha precisa ter pelo menos 8 caracteres.")
    if confirmacao is not None and senha != confirmacao:
        problemas.append("As senhas não são iguais.")
    if consentimento is not None and not consentimento:
        problemas.append("Marque a concordância para criar a conta.")
    return problemas


def mostrarProblemas(problemas):
    for problema in problemas:
        st.warning(problema)


def renderizarEntrada():
    with st.form("entrarForm"):
        email = st.text_input("E-mail", placeholder="nome@exemplo.com").strip().lower()
        senha = st.text_input("Senha", type="password")
        enviado = st.form_submit_button("Entrar", type="primary")

    if not enviado:
        return

    problemas = validarCredenciais(email, senha)
    if problemas:
        mostrarProblemas(problemas)
        return

    try:
        with st.spinner("Entrando..."):
            resposta = entrarNaConta(email, senha)
    except ApiError as erro:
        if erro.codigo == "emailNotVerified":
            definirEtapaAuth("verificar", email)
            reenviarSilencioso(email)
            st.rerun()
        renderizarFaixaErro(str(erro), icone=None)
        return

    iniciarSessaoComHistorico(resposta)


def reenviarSilencioso(email):
    try:
        reenviarCodigo(email)
    except ApiError:
        return


def renderizarCadastro():
    with st.form("cadastroForm"):
        email = st.text_input("E-mail", placeholder="nome@exemplo.com", key="emailCadastro").strip().lower()
        senha = st.text_input("Crie uma senha (mínimo 8 caracteres)", type="password", key="senhaCadastro")
        confirmacao = st.text_input("Repita a senha", type="password")
        consentimento = st.checkbox(
            "Concordo que guardem meu e-mail e o resultado das minhas análises para formar o meu histórico. "
            "Posso apagar tudo quando quiser."
        )
        enviado = st.form_submit_button("Criar conta e receber código", type="primary")

    if not enviado:
        return

    problemas = validarCredenciais(email, senha, confirmacao, consentimento)
    if problemas:
        mostrarProblemas(problemas)
        return

    try:
        with st.spinner("Enviando o código para o seu e-mail..."):
            cadastrarConta(email, senha)
    except ApiError as erro:
        renderizarFaixaErro(str(erro), icone=None)
        return

    definirEtapaAuth("verificar", email)
    st.rerun()


def renderizarVerificacao():
    email = obterEmailPendente()
    st.markdown(f"Enviamos um código de 6 números para **{email}**. Ele vale por 10 minutos.")
    st.caption("Confira também a caixa de spam.")

    with st.form("verificarForm"):
        codigo = st.text_input("Código de verificação", max_chars=6, placeholder="000000").strip()
        enviado = st.form_submit_button("Confirmar e entrar", type="primary")

    if enviado:
        if not (codigo.isdigit() and len(codigo) == 6):
            st.warning("Digite os 6 números do código.")
        else:
            try:
                with st.spinner("Conferindo o código..."):
                    resposta = verificarCodigo(email, codigo)
            except ApiError as erro:
                renderizarFaixaErro(str(erro), icone=None)
            else:
                iniciarSessaoComHistorico(resposta)

    colunaReenviar, colunaVoltar = st.columns(2)
    if colunaReenviar.button("Reenviar código", width="stretch"):
        try:
            reenviarCodigo(email)
            st.success("Pedido enviado. Se o e-mail puder ser confirmado, um novo código chega em instantes.")
        except ApiError as erro:
            renderizarFaixaErro(str(erro), icone=None)
    if colunaVoltar.button("Voltar", width="stretch"):
        definirEtapaAuth("entrar")
        st.rerun()


def renderizarAutenticacao():
    st.subheader("Entre para guardar o seu histórico")
    st.caption("Sua conta guarda só o seu e-mail e o resultado das análises. O texto que você digita não é salvo.")

    if obterEtapaAuth() == "verificar":
        renderizarVerificacao()
        return

    abaEntrar, abaCriar = st.tabs(["Entrar", "Criar conta"])
    with abaEntrar:
        renderizarEntrada()
    with abaCriar:
        renderizarCadastro()
