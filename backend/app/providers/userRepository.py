import uuid

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from app.errors import EmailAlreadyRegisteredError
from app.providers.databaseProvider import (
    agora,
    obterMotor,
    tabelaCodigos,
    tabelaRegistros,
    tabelaSessoes,
    tabelaUsuarios,
)


def criarUsuario(email, hashSenha):
    idUsuario = uuid.uuid4().hex
    try:
        with obterMotor().begin() as conexao:
            conexao.execute(
                insert(tabelaUsuarios).values(
                    id=idUsuario,
                    email=email,
                    passwordHash=hashSenha,
                    verified=False,
                    createdAt=agora(),
                )
            )
    except IntegrityError:
        raise EmailAlreadyRegisteredError() from None
    return idUsuario


def buscarUsuarioPorEmail(email):
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaUsuarios).where(tabelaUsuarios.c.email == email)).first()
    return dict(linha._mapping) if linha else None


def buscarUsuarioPorId(idUsuario):
    with obterMotor().connect() as conexao:
        linha = conexao.execute(select(tabelaUsuarios).where(tabelaUsuarios.c.id == idUsuario)).first()
    return dict(linha._mapping) if linha else None


def atualizarSenha(idUsuario, hashSenha):
    with obterMotor().begin() as conexao:
        conexao.execute(
            update(tabelaUsuarios).where(tabelaUsuarios.c.id == idUsuario).values(passwordHash=hashSenha)
        )


def marcarVerificado(idUsuario):
    with obterMotor().begin() as conexao:
        conexao.execute(update(tabelaUsuarios).where(tabelaUsuarios.c.id == idUsuario).values(verified=True))


def apagarUsuario(idUsuario):
    with obterMotor().begin() as conexao:
        conexao.execute(delete(tabelaRegistros).where(tabelaRegistros.c.userId == idUsuario))
        conexao.execute(delete(tabelaSessoes).where(tabelaSessoes.c.userId == idUsuario))
        conexao.execute(delete(tabelaCodigos).where(tabelaCodigos.c.userId == idUsuario))
        conexao.execute(delete(tabelaUsuarios).where(tabelaUsuarios.c.id == idUsuario))
