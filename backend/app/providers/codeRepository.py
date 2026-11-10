from sqlalchemy import delete, insert, select, update

from app.providers.databaseProvider import obterMotor, tabelaCodigos


def salvarCodigo(idUsuario, hashCodigo, expiraEm, enviadoEm):
    with obterMotor().begin() as conexao:
        conexao.execute(delete(tabelaCodigos).where(tabelaCodigos.c.userId == idUsuario))
        conexao.execute(
            insert(tabelaCodigos).values(
                userId=idUsuario,
                codeHash=hashCodigo,
                expiresAt=expiraEm,
                sentAt=enviadoEm,
                attempts=0,
            )
        )


def buscarCodigo(idUsuario):
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaCodigos).where(tabelaCodigos.c.userId == idUsuario)).first()
    return dict(linha._mapping) if linha else None


def registrarTentativa(idUsuario):
    with obterMotor().begin() as conexao:
        conexao.execute(
            update(tabelaCodigos)
            .where(tabelaCodigos.c.userId == idUsuario)
            .values(attempts=tabelaCodigos.c.attempts + 1)
        )


def apagarCodigo(idUsuario):
    with obterMotor().begin() as conexao:
        conexao.execute(delete(tabelaCodigos).where(tabelaCodigos.c.userId == idUsuario))
