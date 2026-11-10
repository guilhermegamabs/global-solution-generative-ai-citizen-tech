import re
import unicodedata

palavrasVazias = set(
    """
a ao aos as ate com como da das de dela dele deles do dos e ela ele eles em entre era essa esse esta este eu foi
for ha isso isto ja la lhe mais mas me mesmo meu minha muito na nas nem no nos nossa nosso num numa o os ou para pela
pelas pelo pelos por qual quando que quem se sem ser seu seus sua suas so tambem te tem ter um uma umas uns voce voces
vou estou esta estao sao pode posso devo deve fazer faco tenho tive tá ta pra pro
""".split()
)

tamanhoRadical = 6


def removerAcentos(texto):
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(caractere for caractere in decomposto if not unicodedata.combining(caractere))


def normalizar(texto):
    return re.sub(r"\s+", " ", removerAcentos(texto.lower())).strip()


def tokenizar(texto):
    return [
        token[:tamanhoRadical]
        for token in re.findall(r"[a-z0-9]+", normalizar(texto))
        if token not in palavrasVazias and (len(token) > 1 or token.isdigit())
    ]


def dividirFrases(texto):
    partes = re.split(r"(?<=[.!?;])\s+|\n+", texto)
    return [parte.strip() for parte in partes if parte.strip()]
