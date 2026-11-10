import streamlit as st

tamanhoMinimoSintomas = 10


def montarMapaRotulos(itens):
    return {item["value"]: item["label"] for item in itens}


def renderizarFormularioTriagem(opcoes):
    rotulosIdade = montarMapaRotulos(opcoes["ageRanges"])
    rotulosDuracao = montarMapaRotulos(opcoes["durations"])
    rotulosSinais = montarMapaRotulos(opcoes["warningSigns"])

    with st.form("triageForm"):
        sintomas = st.text_area(
            "Descreva o que você está sentindo",
            max_chars=800,
            height=170,
            placeholder="Exemplo: estou com dor de garganta e febre desde ontem à noite.",
            help="Escreva com suas palavras. Não informe nome, CPF ou endereço.",
        )
        faixaEtaria = st.selectbox(
            "Faixa de idade de quem precisa de atendimento",
            list(rotulosIdade),
            format_func=rotulosIdade.get,
            index=2,
        )
        duracao = st.selectbox(
            "Há quanto tempo os sintomas começaram?",
            list(rotulosDuracao),
            format_func=rotulosDuracao.get,
        )
        sinaisAlerta = st.multiselect(
            "Algum destes sinais de alerta está presente? (opcional)",
            list(rotulosSinais),
            format_func=rotulosSinais.get,
            help="Marque somente o que estiver acontecendo agora.",
        )
        temDoencaCronica = st.checkbox(
            "Tenho doença crônica (diabetes, pressão alta, asma, problema no coração...)"
        )
        consentimento = st.checkbox(
            "Entendo que esta orientação não substitui a consulta com um profissional de saúde."
        )
        enviado = st.form_submit_button("Analisar sintomas", type="primary")

    if not enviado:
        return None

    return {
        "carga": {
            "symptoms": sintomas.strip(),
            "ageRange": faixaEtaria,
            "duration": duracao,
            "warningSigns": sinaisAlerta,
            "hasChronicCondition": temDoencaCronica,
        },
        "consentimento": consentimento,
    }


def validarEntrada(envio):
    problemas = []
    sintomas = envio["carga"]["symptoms"]

    if len(sintomas) < tamanhoMinimoSintomas:
        problemas.append("Descreva seus sintomas com pelo menos 10 caracteres.")
    elif not any(caractere.isalpha() for caractere in sintomas):
        problemas.append("Escreva os sintomas com palavras, não apenas números ou símbolos.")

    if not envio["consentimento"]:
        problemas.append("Marque a confirmação de que a orientação não substitui uma consulta.")

    return problemas
