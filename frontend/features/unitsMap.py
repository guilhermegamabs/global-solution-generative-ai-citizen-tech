import math

import plotly.graph_objects as go

from ui.theme import azulProfundo, corTexto, verdeAzulado

larguraMapaPixels = 700
corPosicaoAproximada = "#C26A00"


def calcularZoom(latitude, distanciaMaximaKm):
    larguraKm = max(distanciaMaximaKm, 0.5) * 2 * 1.3
    kmPorPixel = larguraKm / larguraMapaPixels
    zoom = math.log2(156.543 * math.cos(math.radians(latitude)) / kmPorPixel)
    return min(max(zoom, 8), 15)


def montarTracoUnidades(pares, nome, cor):
    return go.Scattermap(
        lat=[unidade["latitude"] for posicao, unidade in pares],
        lon=[unidade["longitude"] for posicao, unidade in pares],
        mode="markers+text",
        marker=dict(size=26, color=cor),
        text=[str(posicao) for posicao, unidade in pares],
        textfont=dict(color="#FFFFFF", size=14),
        name=nome,
        customdata=[
            [unidade["name"], unidade["address"], f'{unidade["distanceKm"]:.1f}'.replace(".", ",")]
            for posicao, unidade in pares
        ],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>A %{customdata[2]} km de você<extra></extra>",
    )


def montarMapaUpas(origem, unidades):
    distanciaMaxima = max(unidade["distanceKm"] for unidade in unidades)
    numeradas = list(enumerate(unidades, start=1))
    confiaveis = [par for par in numeradas if not par[1].get("positionUncertain")]
    aproximadas = [par for par in numeradas if par[1].get("positionUncertain")]

    figura = go.Figure()
    figura.add_trace(
        go.Scattermap(
            lat=[origem["latitude"]],
            lon=[origem["longitude"]],
            mode="markers",
            marker=dict(size=20, color=verdeAzulado),
            name="Você",
            hovertemplate="Região do seu CEP<extra></extra>",
        )
    )
    if confiaveis:
        figura.add_trace(montarTracoUnidades(confiaveis, "UPAs", azulProfundo))
    if aproximadas:
        figura.add_trace(montarTracoUnidades(aproximadas, "UPAs com posição aproximada", corPosicaoAproximada))

    figura.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=origem["latitude"], lon=origem["longitude"]),
            zoom=calcularZoom(origem["latitude"], distanciaMaxima),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=460,
        font=dict(color=corTexto, size=14),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.9)"),
    )
    return figura
