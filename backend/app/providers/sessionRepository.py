from sqlalchemy import delete, insert, select

from app.providers.databaseProvider import agora, obterMotor, tabelaSessoes


def criarSessao(hashToken, idUsuario, expiraEm):
    with obterMotor().begin() as conexao:
        conexao.execute(
            insert(tabelaSessoes).values(
                tokenHash=hashToken,
                userId=idUsuario,
                expiresAt=expiraEm,
                createdAt=agora(),
            )
        )


def buscarSessao(hashToken):
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaSessoes).where(tabelaSessoes.c.tokenHash == hashToken)).first()
    return dict(linha._mapping) if linha else None


def apagarSessao(hashToken):
    with obterMotor().begin() as conexao:
        conexao.execute(delete(tabelaSessoes).where(tabelaSessoes.c.tokenHash == hashToken))
