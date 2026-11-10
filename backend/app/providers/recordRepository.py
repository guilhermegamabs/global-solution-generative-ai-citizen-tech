from datetime import timezone

from sqlalchemy import insert, select, update

from app.providers.databaseProvider import obterMotor, tabelaRegistros
from app.schemas.historySchemas import HistoryItem, ReviewSummary


def salvarRegistro(idUsuario, resposta):
    criadoEm = resposta.createdAt.astimezone(timezone.utc).replace(tzinfo=None)
    with obterMotor().begin() as conexao:
        conexao.execute(
            insert(tabelaRegistros).values(
                id=resposta.recordId,
                userId=idUsuario,
                protocol=resposta.protocol,
                createdAt=criadoEm,
                ageRange=resposta.ageRange.value,
                urgencyLevel=resposta.urgencyLevel.value,
                recommendedService=resposta.recommendedService.value,
                summary=resposta.summary,
                guidance=resposta.guidance,
                warningSignsToWatch=resposta.warningSignsToWatch,
                rationale=resposta.rationale,
                disclaimer=resposta.disclaimer,
            )
        )


def converterLinha(linha):
    revisao = None
    if linha["reviewDecision"]:
        revisao = ReviewSummary(
            decision=linha["reviewDecision"],
            finalUrgency=linha["reviewUrgency"],
            helpful=linha["reviewHelpful"],
        )
    return HistoryItem(
        recordId=linha["id"],
        protocol=linha["protocol"],
        createdAt=linha["createdAt"].replace(tzinfo=timezone.utc),
        ageRange=linha["ageRange"],
        urgencyLevel=linha["urgencyLevel"],
        recommendedService=linha["recommendedService"],
        summary=linha["summary"],
        guidance=linha["guidance"],
        warningSignsToWatch=linha["warningSignsToWatch"],
        rationale=linha["rationale"],
        disclaimer=linha["disclaimer"],
        review=revisao,
    )


def buscarRegistro(idRegistro, idUsuario):
    consulta = select(tabelaRegistros).where(
        tabelaRegistros.c.id == idRegistro, tabelaRegistros.c.userId == idUsuario
    )
    with obterMotor().connect() as conexao:
        linha = conexao.execute(consulta).first()
    return converterLinha(linha._mapping) if linha else None


def listarRegistros(idUsuario):
    consulta = (
        select(tabelaRegistros)
        .where(tabelaRegistros.c.userId == idUsuario)
        .order_by(tabelaRegistros.c.createdAt.desc())
    )
    with obterMotor().connect() as conexao:
        linhas = conexao.execute(consulta).all()
    return [converterLinha(linha._mapping) for linha in linhas]


def salvarRevisao(idRegistro, decisao, urgenciaFinal, util):
    with obterMotor().begin() as conexao:
        conexao.execute(
            update(tabelaRegistros)
            .where(tabelaRegistros.c.id == idRegistro)
            .values(reviewDecision=decisao, reviewUrgency=urgenciaFinal, reviewHelpful=util)
        )
