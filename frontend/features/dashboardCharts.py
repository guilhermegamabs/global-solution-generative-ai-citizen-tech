import plotly.graph_objects as go

from ui.theme import azulPrimario, corTexto, estilosUrgencia, ordemUrgencia, rotulosFaixaCurtos, rotulosServico

fonteGrafico = dict(family="Source Sans, sans-serif", color=corTexto, size=14)


def aplicarLayout(figura, titulo):
    figura.update_layout(
        title=dict(text=titulo, font=dict(size=17)),
        font=fonteGrafico,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F6FAFE",
        margin=dict(l=20, r=20, t=60, b=30),
        height=340,
    )
    return figura


def montarBarrasUrgencia(tabela):
    contagem = tabela["urgencyLevel"].value_counts()
    rotulos = [f'{estilosUrgencia[nivel]["icone"]} {estilosUrgencia[nivel]["rotulo"]}' for nivel in ordemUrgencia]
    valores = [int(contagem.get(nivel, 0)) for nivel in ordemUrgencia]
    cores = [estilosUrgencia[nivel]["grafico"] for nivel in ordemUrgencia]
    figura = go.Figure(
        go.Bar(
            x=rotulos,
            y=valores,
            marker=dict(color=cores),
            text=valores,
            textposition="outside",
            hovertemplate="%{x}<br>%{y} solicitações<extra></extra>",
        )
    )
    figura.update_yaxes(title="Solicitações", dtick=1, rangemode="tozero")
    return aplicarLayout(figura, "Solicitações por nível de urgência")


def montarLinhaTempo(tabela):
    ordenada = tabela.sort_values("createdAt")
    posicoes = [ordemUrgencia.index(nivel) for nivel in ordenada["urgencyLevel"]]
    cores = [estilosUrgencia[nivel]["grafico"] for nivel in ordenada["urgencyLevel"]]
    figura = go.Figure(
        go.Scatter(
            x=ordenada["createdAt"],
            y=posicoes,
            mode="lines+markers",
            line=dict(color=azulPrimario, width=2),
            marker=dict(color=cores, size=13, line=dict(color=azulPrimario, width=1)),
            customdata=ordenada[["protocol"]],
            hovertemplate="%{customdata[0]}<br>%{x|%d/%m %H:%M}<extra></extra>",
        )
    )
    figura.update_yaxes(
        tickmode="array",
        tickvals=list(range(len(ordemUrgencia))),
        ticktext=[estilosUrgencia[nivel]["rotulo"] for nivel in ordemUrgencia],
        range=[-0.5, len(ordemUrgencia) - 0.5],
    )
    return aplicarLayout(figura, "Linha do tempo das solicitações")


def montarRoscaServico(tabela):
    contagem = tabela["recommendedService"].value_counts()
    figura = go.Figure(
        go.Pie(
            labels=[rotulosServico[chave] for chave in contagem.index],
            values=contagem.values,
            hole=0.55,
            marker=dict(colors=["#0B5FA5", "#0E8FA0", "#5BA4E0", "#073B6B"]),
            hovertemplate="%{label}<br>%{value} (%{percent})<extra></extra>",
        )
    )
    return aplicarLayout(figura, "Serviço de saúde recomendado")


def montarBarrasIdade(tabela):
    contagem = tabela["ageRange"].value_counts()
    figura = go.Figure(
        go.Bar(
            x=[rotulosFaixaCurtos[chave] for chave in contagem.index],
            y=contagem.values,
            marker=dict(color=azulPrimario),
            hovertemplate="%{x}<br>%{y} solicitações<extra></extra>",
        )
    )
    figura.update_yaxes(title="Solicitações", dtick=1, rangemode="tozero")
    return aplicarLayout(figura, "Solicitações por faixa de idade")
