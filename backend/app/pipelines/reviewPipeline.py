from app.errors import InvalidReviewError, RecordNotFoundError
from app.providers.recordRepository import buscarRegistro, salvarRevisao
from app.schemas.reviewSchemas import ReviewDecision, ReviewResponse


def executarRevisao(revisao, idUsuario):
    registro = buscarRegistro(revisao.recordId, idUsuario)
    if registro is None:
        raise RecordNotFoundError()

    ehCorrecao = revisao.decision == ReviewDecision.corrected
    if ehCorrecao and revisao.correctedUrgency is None:
        raise InvalidReviewError()

    urgenciaFinal = revisao.correctedUrgency if ehCorrecao else registro.urgencyLevel
    salvarRevisao(revisao.recordId, revisao.decision.value, urgenciaFinal.value, revisao.helpful)

    return ReviewResponse(
        recordId=registro.recordId,
        protocol=registro.protocol,
        decision=revisao.decision,
        finalUrgency=urgenciaFinal,
        status="registered",
    )
