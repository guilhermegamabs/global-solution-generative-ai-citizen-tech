import re

from app.rag.textUtils import dividirFrases, normalizar, tokenizar

padroesInjecao = [
    r"ignor\w* (todas |as |os |suas )*(instruc|regras|orientac|fontes|comandos)",
    r"desconsider\w* (todas |as |os |suas )*(instruc|regras|orientac)",
    r"esquec\w* (todas |as |os |suas )*(instruc|regras)",
    r"(revele|mostre|repita|imprima|escreva|liste|exiba)\b.{0,40}\b(prompt|instruc\w* (do|de) sistema|regras que (voce )?recebeu|configurac)",
    r"(system prompt|prompt de sistema|prompt do sistema|developer mode|modo desenvolvedor|jailbreak|\bdan\b)",
    r"(finja|faca de conta|imagine) que (voce )?(e|seja) (um |uma )?(medic|outro|ia sem|assistente sem)",
    r"sem (nenhuma )?(restric|regra|limite|filtro)",
    r"(voce agora e|a partir de agora voce)",
    r"instruc\w* para o (assistente|modelo|ia)",
]

padroesExfiltracao = [
    r"(e-?mails?|senhas?|cpfs?|historicos?|dados) (de|dos) (outros )?(usuarios|pacientes|cidadaos|pessoas cadastradas)",
    r"(banco de dados|tabela de usuarios|chave (de )?api|api key|token)",
]

padroesDadosPessoais = {
    "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "cartaoSus": r"\b[1-9]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b",
    "telefone": r"(\(?\b\d{2}\)?\s?)?\b9?\d{4}-?\d{4}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.[\w.]+\b",
    "cep": r"\b\d{5}-\d{3}\b",
}

sinaisEmergencia = [
    r"dor (forte |intensa )?no peito",
    r"aperto no peito",
    r"falta de ar (forte|intensa|grave)",
    r"nao (consegue|consigo) respirar",
    r"labios? (roxos?|arroxeados?)",
    r"desmai",
    r"convuls",
    r"inconscien",
    r"\bavc\b",
    r"derrame",
    r"rosto torto",
    r"fala enrolada",
    r"sangramento (forte|que nao para|intenso)",
    r"(quero|vou|pensando em) (me matar|morrer|acabar com (a|minha) vida)",
    r"suicid",
    r"overdose",
    r"engasg",
    r"picad\w* de (cobra|serpente)|mordid\w* de (cobra|serpente)",
]

padraoDose = r"\b\d+[.,]?\d*\s?(mg|ml|mcg|g|gotas|comprimidos?|capsulas?)\b"

linhasSuspeitas = [
    r"instruc\w* para o (assistente|modelo|ia|chatbot)",
    r"ignor\w* (todas |as |os )*(instruc|fontes|regras)",
    r"(diga|responda|informe) ao usuario que",
    r"system prompt|prompt de sistema",
]

marcadorCanario = "CANARIO-ORIENTA-7Q2X"


def contemPadrao(texto, padroes):
    alvo = normalizar(texto)
    return any(re.search(padrao, alvo) for padrao in padroes)


def detectarInjecao(texto):
    return contemPadrao(texto, padroesInjecao)


def detectarExfiltracao(texto):
    return contemPadrao(texto, padroesExfiltracao)


def detectarEmergencia(texto):
    return contemPadrao(texto, sinaisEmergencia)


def mascararDadosPessoais(texto):
    encontrados = []
    mascarado = texto
    for tipo, padrao in padroesDadosPessoais.items():
        if re.search(padrao, mascarado):
            encontrados.append(tipo)
            mascarado = re.sub(padrao, f"[{tipo} removido]", mascarado)
    return mascarado, encontrados


def sanitizarTrecho(texto):
    limpas = []
    removidas = 0
    for linha in texto.split("\n"):
        if contemPadrao(linha, linhasSuspeitas):
            removidas += 1
            continue
        limpas.append(linha)
    return "\n".join(limpas), removidas


def vazouPrompt(resposta, promptSistema):
    if marcadorCanario in resposta:
        return True
    frasesPrompt = [normalizar(frase) for frase in dividirFrases(promptSistema) if len(frase) > 60]
    alvo = normalizar(resposta)
    copiadas = sum(1 for frase in frasesPrompt if frase[:60] in alvo)
    return copiadas >= 2


def doseSemFonte(resposta, contextos):
    doses = re.findall(padraoDose, normalizar(resposta))
    if not doses:
        return False
    contexto = normalizar(" ".join(contextos))
    return not re.search(padraoDose, contexto)


def calcularSuporte(resposta, contextos):
    frases = [frase for frase in dividirFrases(resposta) if len(tokenizar(frase)) >= 4]
    if not frases:
        return 1.0
    vocabulario = set(tokenizar(" ".join(contextos)))
    if not vocabulario:
        return 0.0
    coberturas = []
    for frase in frases:
        tokens = set(tokenizar(frase))
        coberturas.append(len(tokens & vocabulario) / len(tokens))
    return sum(coberturas) / len(coberturas)
