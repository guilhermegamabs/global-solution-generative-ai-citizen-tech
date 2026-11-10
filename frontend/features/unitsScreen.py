import streamlit as st

from features.unitsMap import montarMapaUpas
from providers.apiClient import ApiError, buscarUpasProximas
from state.sessionState import definirBuscaUpas, obterBuscaUpas
from ui.components import renderizarCartaoUnidade, renderizarEstadoVazio, renderizarFaixaErro


quantidadeUpas = 10


def extrairNumeros(texto):
    return "".join(caractere for caractere in texto if caractere.isdigit())


def renderizarFormularioCep():
    with st.form("upasForm"):
        cep = st.text_input(
            "Seu CEP",
            max_chars=9,
            placeholder="Exemplo: 01310-100",
            help="Digite só o CEP. Não digite rua e número.",
        )
        enviado = st.form_submit_button("Buscar UPAs", type="primary")

    if not enviado:
        return None
    return {"cep": extrairNumeros(cep)}


def processarBusca(envio):
    if len(envio["cep"]) != 8:
        st.warning("Digite o CEP com 8 números, por exemplo 01310-100.", icon="✏️")
        return

    try:
        with st.spinner("Procurando as UPAs mais próximas..."):
            resultado = buscarUpasProximas(envio["cep"], quantidadeUpas)
    except ApiError as erro:
        renderizarFaixaErro(str(erro))
        return

    definirBuscaUpas(resultado)


def renderizarResultadoUpas(resultado):
    origem = resultado["origin"]
    unidades = resultado["units"]
    local = ", ".join(parte for parte in (origem["neighborhood"], f'{origem["city"]}-{origem["state"]}') if parte)
    st.markdown(f"**{len(unidades)} UPAs mais próximas de {local}**")
    if origem.get("approximate"):
        st.warning(
            "Não encontramos a sua rua no mapa. As distâncias foram calculadas a partir do centro da cidade "
            "e podem não refletir a sua localização.",
            icon="📍",
        )

    colunaLista, colunaMapa = st.columns([1, 1.4], gap="large")
    with colunaLista:
        for posicao, unidade in enumerate(unidades, start=1):
            renderizarCartaoUnidade(posicao, unidade, f'{origem["city"]}, {origem["state"]}')
    with colunaMapa:
        st.plotly_chart(montarMapaUpas(origem, unidades), width="stretch")

    st.caption("Fonte: CNES. Confirme telefone e horário antes de ir.")


def renderizarUpas():
    st.subheader("UPAs mais próximas de você")
    st.caption("🔒 Usamos só o CEP e não guardamos. Em emergência, ligue 192.")

    envio = renderizarFormularioCep()
    if envio:
        processarBusca(envio)

    resultado = obterBuscaUpas()
    if resultado:
        renderizarResultadoUpas(resultado)
    else:
        renderizarEstadoVazio("🗺️", "Nenhuma busca ainda", "Digite seu CEP e clique em Buscar UPAs para ver o mapa.")
