import streamlit as st

azulPrimario = "#0B5FA5"
azulProfundo = "#073B6B"
azulSuave = "#EAF3FC"
verdeAzulado = "#0E8FA0"
corTexto = "#0F2A43"

ordemUrgencia = ["low", "medium", "high", "emergency"]

estilosUrgencia = {
    "low": {"rotulo": "Baixa", "icone": "✔", "cor": "#0B5A36", "fundo": "#E3F6EC", "borda": "#1B8A5A", "grafico": "#1B8A5A"},
    "medium": {"rotulo": "Moderada", "icone": "ℹ", "cor": "#5E4300", "fundo": "#FFF6DB", "borda": "#D9A300", "grafico": "#D9A300"},
    "high": {"rotulo": "Alta", "icone": "⬆", "cor": "#7A3200", "fundo": "#FFE9D6", "borda": "#E8710A", "grafico": "#E8710A"},
    "emergency": {"rotulo": "Emergência", "icone": "🚑", "cor": "#8F1414", "fundo": "#FDE4E4", "borda": "#D32F2F", "grafico": "#D32F2F"},
}

significadosUrgencia = {
    "low": "Você pode cuidar em casa ou marcar uma consulta.",
    "medium": "Procure a Unidade Básica de Saúde em até 2 dias.",
    "high": "Procure uma UPA ainda hoje.",
    "emergency": "Ligue 192 (SAMU) agora.",
}

rotulosServico = {
    "selfCare": "🏠 Cuidado em casa",
    "basicUnit": "🏥 Unidade Básica de Saúde (UBS)",
    "urgentCare": "🏨 UPA 24 horas",
    "ambulance": "🚑 SAMU — ligue 192",
}

rotulosDecisao = {
    "confirmed": "Confirmo o resultado",
    "corrected": "Quero corrigir a urgência",
    "pending": "Sem revisão",
}

rotulosFaixaCurtos = {
    "child": "Criança",
    "teen": "Adolescente",
    "adult": "Adulto",
    "senior": "Idoso",
}

estilosConfianca = {
    "high": {"rotulo": "Confiança alta", "icone": "✔", "cor": "#0B5A36", "fundo": "#E3F6EC", "borda": "#1B8A5A"},
    "medium": {"rotulo": "Confiança média", "icone": "ℹ", "cor": "#073B6B", "fundo": "#EAF3FC", "borda": "#0B5FA5"},
    "low": {"rotulo": "Confiança baixa", "icone": "⚠", "cor": "#5E4300", "fundo": "#FFF6DB", "borda": "#D9A300"},
    "none": {"rotulo": "Sem resposta", "icone": "✋", "cor": "#3E5B78", "fundo": "#F1F4F8", "borda": "#8BA3BC"},
}

significadosConfianca = {
    "high": "As fontes encontradas tratam bem da pergunta e a resposta segue o texto delas.",
    "medium": "A resposta tem fonte, mas confira o trecho original antes de decidir.",
    "low": "A ligação entre resposta e fonte é fraca. Confirme na Unidade Básica de Saúde.",
    "none": "Não houve fonte suficiente ou o pedido estava fora do que o assistente faz.",
}

rotulosTemas = {
    "redeDeAtendimento": "Onde ser atendido (UBS, UPA, SAMU, CAPS)",
    "servicosDoSus": "Serviços do SUS (Farmácia Popular, Meu SUS Digital, Ouvidoria)",
    "vacinacao": "Vacinação",
    "emergencias": "Emergências (AVC, infarto, picada de cobra)",
    "saudeMental": "Saúde mental",
    "doencas": "Doenças (dengue, gripe, sarampo e outras)",
    "doencasCronicas": "Doenças crônicas (pressão alta, diabetes, asma)",
    "ciclosDeVida": "Gravidez",
}

folhaEstilo = f"""
<style>
.block-container {{ padding-top: 1.5rem; max-width: 1200px; }}
.appHeader {{
    background: linear-gradient(120deg, {azulProfundo} 0%, {azulPrimario} 60%, {verdeAzulado} 100%);
    color: #FFFFFF;
    padding: 1.4rem 1.6rem;
    border-radius: 14px;
    margin-bottom: 1rem;
}}
.appHeader h1 {{ color: #FFFFFF; margin: 0; font-size: 1.9rem; padding: 0; }}
.appHeader p {{ margin: 0.3rem 0 0 0; font-size: 1.05rem; color: #EAF3FC; }}
.urgencyBadge {{
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 999px;
    font-weight: 700;
    border: 2px solid;
    font-size: 0.95rem;
}}
.urgencyBadge.large {{ font-size: 1.3rem; padding: 0.45rem 1.1rem; }}
.infoCard {{
    background: {azulSuave};
    border-left: 6px solid {azulPrimario};
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
    color: {corTexto};
}}
.infoCard h4 {{ margin: 0 0 0.4rem 0; font-size: 1.05rem; color: {azulProfundo}; }}
.infoCard ul {{ margin: 0; padding-left: 1.2rem; }}
.infoCard li {{ margin: 0.2rem 0; }}
.metricCard {{
    background: #FFFFFF;
    border: 1px solid #C9DDF0;
    border-top: 5px solid {azulPrimario};
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    color: {corTexto};
}}
.metricCard .metricValue {{ font-size: 1.9rem; font-weight: 800; color: {azulProfundo}; line-height: 1.1; }}
.metricCard .metricLabel {{ font-weight: 600; }}
.metricCard .metricHint {{ font-size: 0.85rem; color: #3E5B78; }}
.emptyState {{
    text-align: center;
    padding: 2rem 1rem;
    border: 2px dashed #9CC2E5;
    border-radius: 12px;
    background: #F6FAFE;
    color: {corTexto};
}}
.emptyState .emptyIcon {{ font-size: 2.4rem; }}
.protocolCard {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    background: #FFFFFF;
    border: 1px solid #C9DDF0;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin: 0.8rem 0 0.5rem 0;
    color: {corTexto};
}}
.protocolCard .protocolLabel {{ font-size: 0.85rem; font-weight: 600; color: #3E5B78; }}
.protocolCard .protocolCode {{ font-family: monospace; font-size: 1.15rem; font-weight: 800; color: {azulProfundo}; letter-spacing: 0.04em; }}
.noticeCard {{
    background: #F6FAFE;
    border: 1px solid #C9DDF0;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0 1rem 0;
    font-size: 0.92rem;
    line-height: 1.45;
    color: #26425E;
}}
.confirmCard {{
    background: #E3F6EC;
    border: 2px solid #1B8A5A;
    border-radius: 10px;
    padding: 0.9rem 1rem;
    margin: 0.8rem 0;
    color: #0B5A36;
}}
.confirmCard strong {{ font-size: 1.05rem; }}
.confirmCard .confirmLine {{ margin-top: 0.35rem; }}
.unitCard {{
    display: flex;
    gap: 0.8rem;
    background: #FFFFFF;
    border: 1px solid #C9DDF0;
    border-left: 6px solid {azulProfundo};
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    margin: 0.5rem 0;
    color: {corTexto};
}}
.unitCard .unitNumber {{
    flex: 0 0 2rem;
    height: 2rem;
    border-radius: 50%;
    background: {azulProfundo};
    color: #FFFFFF;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.unitCard .unitName {{ font-weight: 800; color: {azulProfundo}; }}
.unitCard .unitMeta {{ font-size: 0.92rem; margin-top: 0.15rem; }}
.unitCard .unitWarning {{ color: #7A3200; font-weight: 600; }}
.unitCard a {{ color: {azulPrimario}; font-weight: 700; }}
.alertBanner {{
    border: 2px solid #D32F2F;
    background: #FDE4E4;
    color: #8F1414;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}}
.sourceCard {{
    background: #FFFFFF;
    border: 1px solid #C9DDF0;
    border-left: 6px solid {verdeAzulado};
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    margin: 0.45rem 0;
    color: {corTexto};
    font-size: 0.92rem;
}}
.sourceCard .sourceTitle {{ font-weight: 800; color: {azulProfundo}; }}
.sourceCard .sourceMeta {{ font-size: 0.82rem; color: #3E5B78; margin: 0.15rem 0 0.35rem 0; }}
.sourceCard .sourceExcerpt {{ white-space: pre-line; }}
.sourceCard a {{ color: {azulPrimario}; font-weight: 700; }}
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="tab"]:focus-visible {{
    outline: 3px solid #F5A623 !important;
    outline-offset: 2px;
}}
</style>
"""


def aplicarTema():
    st.markdown(folhaEstilo, unsafe_allow_html=True)
