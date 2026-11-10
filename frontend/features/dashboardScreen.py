import streamlit as st

from features.dashboardCharts import montarBarrasIdade, montarBarrasUrgencia, montarLinhaTempo, montarRoscaServico
from state.recordFrame import paraTabela
from state.sessionState import obterRegistros
from ui.components import renderizarCartaoMetrica, renderizarEstadoVazio
from ui.theme import estilosUrgencia, ordemUrgencia, rotulosFaixaCurtos, rotulosServico


def formatarUrgencia(nivel):
    estilo = estilosUrgencia[nivel]
    return f'{estilo["icone"]} {estilo["rotulo"]}'


def renderizarFiltros():
    colunaUrgencia, colunaServico, colunaIdade = st.columns(3)
    urgencias = colunaUrgencia.multiselect(
        "Nível de urgência",
        ordemUrgencia,
        default=ordemUrgencia,
        format_func=formatarUrgencia,
    )
    servicos = colunaServico.multiselect(
        "Serviço recomendado",
        list(rotulosServico),
        default=list(rotulosServico),
        format_func=rotulosServico.get,
    )
    idades = colunaIdade.multiselect(
        "Faixa de idade",
        list(rotulosFaixaCurtos),
        default=list(rotulosFaixaCurtos),
        format_func=rotulosFaixaCurtos.get,
    )
    return urgencias, servicos, idades


def aplicarFiltros(tabela, urgencias, servicos, idades):
    mascara = (
        tabela["urgencyLevel"].isin(urgencias)
        & tabela["recommendedService"].isin(servicos)
        & tabela["ageRange"].isin(idades)
    )
    return tabela[mascara]


def renderizarMetricas(tabela):
    total = len(tabela)
    urgentes = int(tabela["urgencyLevel"].isin(["high", "emergency"]).sum())
    revisadas = int((tabela["reviewStatus"] != "pending").sum())
    corrigidas = int((tabela["reviewStatus"] == "corrected").sum())

    colunas = st.columns(4)
    with colunas[0]:
        renderizarCartaoMetrica("Solicitações", total, "no filtro atual")
    with colunas[1]:
        renderizarCartaoMetrica("Urgência alta ou emergência", urgentes, "exigem atenção rápida")
    with colunas[2]:
        renderizarCartaoMetrica("Revisadas por você", revisadas, "confirmadas ou corrigidas")
    with colunas[3]:
        renderizarCartaoMetrica("Corrigidas", corrigidas, "a IA foi ajustada por pessoas")


def renderizarPainel():
    st.subheader("Painel de acompanhamento")
    registros = obterRegistros()

    if not registros:
        renderizarEstadoVazio("📊", "Sem dados ainda", "Faça uma análise na aba Triagem para ver os gráficos.")
        return

    urgencias, servicos, idades = renderizarFiltros()
    tabela = aplicarFiltros(paraTabela(registros), urgencias, servicos, idades)

    if tabela.empty:
        renderizarEstadoVazio("🔎", "Nada para mostrar", "Nenhuma solicitação combina com os filtros escolhidos.")
        return

    renderizarMetricas(tabela)

    esquerda, direita = st.columns(2)
    with esquerda:
        st.plotly_chart(montarBarrasUrgencia(tabela), width="stretch")
        st.plotly_chart(montarLinhaTempo(tabela), width="stretch")
    with direita:
        st.plotly_chart(montarRoscaServico(tabela), width="stretch")
        st.plotly_chart(montarBarrasIdade(tabela), width="stretch")
