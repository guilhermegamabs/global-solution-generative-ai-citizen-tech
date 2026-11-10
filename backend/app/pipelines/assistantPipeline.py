import re
import time
from dataclasses import dataclass

from pydantic import ValidationError

from app.config import obterModeloAssistente
from app.errors import InvalidModelResponseError
from app.rag import guardrails
from app.rag.prompts import montarMensagemUsuario, prompts
from app.rag.textUtils import normalizar, tokenizar
from app.schemas.assistantSchemas import (
    AnswerStatus,
    AssistantModelOutput,
    AssistantResponse,
    Confidence,
    Diagnostics,
    SourceItem,
)

avisoLegal = (
    "Respostas baseadas em páginas do Ministério da Saúde. Não substituem a avaliação de um profissional de saúde."
)
avisoEmergencia = "Isso pode ser uma emergência. Ligue agora para o SAMU no 192, de graça, de qualquer telefone."

mensagemSemEvidencia = (
    "Não encontrei essa informação nas fontes oficiais de saúde que eu consulto, então prefiro não responder para não errar. "
    "Eu tiro dúvidas sobre saúde e serviços do SUS. Para casos específicos, procure a Unidade Básica de Saúde "
    "mais próxima ou ligue para a Ouvidoria do SUS no 136."
)
mensagemEmergenciaSemFonte = (
    "Pelo que você descreveu, não espere: ligue agora para o SAMU no 192. "
    "Enquanto isso, fique com a pessoa e siga as orientações de quem atender a ligação."
)
mensagemRemedio = (
    "Não indico remédio nem dose: isso precisa ser orientado por médico, enfermeiro ou farmacêutico, "
    "que conhecem o seu caso. Procure a Unidade Básica de Saúde ou converse com o farmacêutico."
)
padraoPedidoRemedio = r"\b(dose|dosagem|quantos? (mg|ml|gotas|comprimidos)|que remedio|qual remedio|posso tomar|me receite|receita de remedio|antibiotico)"
mensagemBloqueio = (
    "Não posso mudar minhas regras, revelar minhas instruções nem acessar dados de outras pessoas. "
    "Se tiver uma dúvida sobre saúde ou sobre o SUS, é só perguntar."
)
mensagemForaDoEscopo = "Eu só respondo dúvidas sobre saúde e serviços do SUS. Quer perguntar algo sobre isso?"

palavrasDeContinuacao = {"e", "isso", "ele", "ela", "dele", "dela", "nesse", "nisso", "entao", "tambem", "mesmo"}
tentativasSaida = 2
turnosDeContexto = 2
limiarAutonoma = 0.5


@dataclass
class OpcoesAssistente:
    prompt: str = "final"
    protecoes: bool = True
    k: int = 5
    limiarRecuperacao: float = 0.12
    limiarSuporte: float = 0.45
    modelo: str | None = None


def montarConsulta(pergunta, historico, base=None):
    perguntasAnteriores = [turno["content"] for turno in historico if turno["role"] == "user"]
    if not perguntasAnteriores:
        return pergunta
    palavras = normalizar(pergunta).split()
    curta = len(tokenizar(pergunta)) <= 4
    continua = bool(palavras) and palavras[0] in palavrasDeContinuacao
    combinada = " ".join([*perguntasAnteriores[-turnosDeContexto:], pergunta])
    if not (continua or curta):
        return pergunta
    if base is None:
        return combinada
    if not continua:
        sozinha = base.buscar(pergunta, 1)
        if sozinha and sozinha[0].pontuacao >= limiarAutonoma:
            return pergunta
    candidatas = [combinada] + [f"{anterior} {pergunta}" for anterior in reversed(perguntasAnteriores[-3:])]
    melhor, melhorPontuacao = combinada, -1.0
    for candidata in dict.fromkeys(candidatas):
        resultados = base.buscar(candidata, 1)
        pontuacao = resultados[0].pontuacao if resultados else 0.0
        if pontuacao > melhorPontuacao:
            melhor, melhorPontuacao = candidata, pontuacao
    return melhor


def removerCitacoes(texto):
    return re.sub(r"\[\d+(,\s*\d+)*\]", "", texto)


def montarFonte(numero, resultado):
    trecho = resultado.trecho
    return SourceItem(
        number=numero,
        chunkId=trecho.chunkId,
        title=trecho.titulo,
        section=trecho.secao,
        url=trecho.url,
        accessedAt=trecho.acessadoEm,
        excerpt=trecho.texto[:400],
        score=round(resultado.pontuacao, 4),
    )


def definirConfianca(topo, suporte):
    if topo >= 0.5 and suporte >= 0.7:
        return Confidence.high
    if suporte >= 0.55:
        return Confidence.medium
    return Confidence.low


def obterSaidaDoModelo(gerar, promptSistema, mensagem):
    for tentativa in range(tentativasSaida):
        try:
            saida = AssistantModelOutput(**gerar(promptSistema, mensagem))
        except (ValidationError, TypeError, InvalidModelResponseError):
            continue
        if not saida.resposta.strip():
            if saida.foraDoEscopo:
                return saida.model_copy(update={"resposta": mensagemForaDoEscopo})
            if saida.semEvidencia:
                return saida.model_copy(update={"resposta": mensagemSemEvidencia})
            continue
        return saida
    raise InvalidModelResponseError()


class Resposta:
    def __init__(self, base, opcoes, consulta, inicio):
        self.base = base
        self.opcoes = opcoes
        self.consulta = consulta
        self.inicio = inicio
        self.alertas = []
        self.emergencia = None
        self.topo = 0.0
        self.suporte = None

    def montar(self, texto, status, confianca, fontes):
        return AssistantResponse(
            answer=texto,
            status=status,
            confidence=confianca,
            sources=fontes,
            emergencyNotice=self.emergencia,
            alerts=self.alertas,
            diagnostics=Diagnostics(
                searchQuery=self.consulta,
                topScore=round(self.topo, 4),
                support=None if self.suporte is None else round(self.suporte, 3),
                retriever=self.base.buscador.nome,
                chunking=self.base.configuracao.chave,
                model=self.opcoes.modelo or obterModeloAssistente(),
                latencyMs=int((time.perf_counter() - self.inicio) * 1000),
            ),
            disclaimer=avisoLegal,
        )


def responderPergunta(pergunta, historico, gerar, base, opcoes=None, tema=None):
    opcoes = opcoes or OpcoesAssistente()
    inicio = time.perf_counter()
    historico = [dict(turno) for turno in historico]

    perguntaUsada = pergunta
    dadosRemovidos = []
    if opcoes.protecoes:
        perguntaUsada, dadosRemovidos = guardrails.mascararDadosPessoais(pergunta)
        historico = [
            {**turno, "content": guardrails.mascararDadosPessoais(turno["content"])[0]} for turno in historico
        ]
    consulta = montarConsulta(perguntaUsada, historico, base)
    saida = Resposta(base, opcoes, consulta, inicio)

    if opcoes.protecoes:
        if dadosRemovidos:
            saida.alertas.append("personalDataRemoved")
        if guardrails.detectarEmergencia(pergunta):
            saida.emergencia = avisoEmergencia
        if guardrails.detectarInjecao(pergunta) or guardrails.detectarExfiltracao(pergunta):
            saida.alertas.append("manipulationAttempt")
            return saida.montar(mensagemBloqueio, AnswerStatus.blocked, Confidence.none, [])

    resultados = base.buscar(consulta, opcoes.k, tema)
    saida.topo = resultados[0].pontuacao if resultados else 0.0

    if opcoes.protecoes and saida.topo < opcoes.limiarRecuperacao:
        saida.alertas.append("lowRetrievalScore")
        if saida.emergencia:
            texto = mensagemEmergenciaSemFonte
        elif re.search(padraoPedidoRemedio, normalizar(pergunta)):
            texto = mensagemRemedio
        else:
            texto = mensagemSemEvidencia
        return saida.montar(texto, AnswerStatus.abstained, Confidence.none, [])

    trechosPrompt = []
    for resultado in resultados:
        trecho = resultado.trecho
        if opcoes.protecoes:
            textoLimpo, removidas = guardrails.sanitizarTrecho(trecho.texto)
            if removidas:
                saida.alertas.append("suspiciousSourceLineRemoved")
                trecho = type(trecho)(**{**trecho.__dict__, "texto": textoLimpo})
        trechosPrompt.append(trecho)

    promptSistema = prompts[opcoes.prompt]
    mensagem = montarMensagemUsuario(perguntaUsada, trechosPrompt, historico)
    modelo = obterSaidaDoModelo(gerar, promptSistema, mensagem)

    if opcoes.protecoes and guardrails.vazouPrompt(modelo.resposta, prompts["final"]):
        saida.alertas.append("promptLeakBlocked")
        return saida.montar(mensagemBloqueio, AnswerStatus.blocked, Confidence.none, [])

    if modelo.foraDoEscopo:
        return saida.montar(
            modelo.resposta if not opcoes.protecoes else mensagemForaDoEscopo,
            AnswerStatus.outOfScope,
            Confidence.none,
            [],
        )

    numerosValidos = sorted({numero for numero in modelo.fontesUsadas if 1 <= numero <= len(resultados)})
    fontes = [montarFonte(numero, resultados[numero - 1]) for numero in numerosValidos]

    if modelo.semEvidencia:
        texto = mensagemSemEvidencia if opcoes.protecoes else modelo.resposta
        return saida.montar(texto, AnswerStatus.abstained, Confidence.none, [])

    contextosCitados = [trechosPrompt[numero - 1].texto for numero in numerosValidos]
    saida.suporte = guardrails.calcularSuporte(removerCitacoes(modelo.resposta), contextosCitados)

    if opcoes.protecoes:
        if not numerosValidos:
            saida.alertas.append("noValidCitation")
            return saida.montar(mensagemSemEvidencia, AnswerStatus.abstained, Confidence.none, [])
        if guardrails.doseSemFonte(modelo.resposta, contextosCitados):
            saida.alertas.append("unsupportedDoseBlocked")
            return saida.montar(mensagemSemEvidencia, AnswerStatus.abstained, Confidence.none, [])
        if saida.suporte < opcoes.limiarSuporte:
            saida.alertas.append("lowSupport")
            return saida.montar(mensagemSemEvidencia, AnswerStatus.abstained, Confidence.none, [])

    confianca = definirConfianca(saida.topo, saida.suporte)
    return saida.montar(modelo.resposta, AnswerStatus.answered, confianca, fontes)
