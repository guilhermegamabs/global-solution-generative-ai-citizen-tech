import streamlit as st

from ui.components import renderizarCartaoInfo


def renderizarSobre():
    st.subheader("Sobre o Orienta Saúde")
    st.write(
        "O Orienta Saúde ajuda você a entender, em linguagem simples, se o que está sentindo "
        "pede cuidado em casa, uma Unidade Básica de Saúde, uma UPA ou o SAMU."
    )
    renderizarCartaoInfo(
        "O que ele faz",
        [
            "Classifica a urgência do seu relato.",
            "Indica o tipo de serviço de saúde mais adequado.",
            "Explica o que fazer agora e quais sinais pedem ajuda imediata.",
        ],
        "✅",
    )
    renderizarCartaoInfo(
        "O que ele NÃO faz",
        [
            "Não faz diagnóstico.",
            "Não indica remédios nem doses.",
            "Não substitui consulta com médico ou enfermeiro.",
        ],
        "🚫",
    )
    renderizarCartaoInfo(
        "Sua privacidade",
        [
            "Não digite nome, CPF ou endereço no relato.",
            "Guardamos só o seu e-mail e o resultado das análises. O texto que você escreve não é salvo.",
            "Você pode apagar a conta e todo o histórico no menu lateral.",
        ],
        "🔒",
    )
