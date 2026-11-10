from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.pool import StaticPool

from app.config import obterUrlBanco

metadados = MetaData()

tabelaUsuarios = Table(
    "users",
    metadados,
    Column("id", String(32), primary_key=True),
    Column("email", String(254), nullable=False, unique=True),
    Column("passwordHash", String(256), nullable=False),
    Column("verified", Boolean, nullable=False, default=False),
    Column("createdAt", DateTime, nullable=False),
)

tabelaCodigos = Table(
    "verificationCodes",
    metadados,
    Column("userId", String(32), ForeignKey("users.id"), primary_key=True),
    Column("codeHash", String(64), nullable=False),
    Column("expiresAt", DateTime, nullable=False),
    Column("sentAt", DateTime, nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
)

tabelaSessoes = Table(
    "sessions",
    metadados,
    Column("tokenHash", String(64), primary_key=True),
    Column("userId", String(32), ForeignKey("users.id"), nullable=False, index=True),
    Column("expiresAt", DateTime, nullable=False),
    Column("createdAt", DateTime, nullable=False),
)

tabelaRegistros = Table(
    "triageRecords",
    metadados,
    Column("id", String(32), primary_key=True),
    Column("userId", String(32), ForeignKey("users.id"), nullable=False, index=True),
    Column("protocol", String(40), nullable=False),
    Column("createdAt", DateTime, nullable=False),
    Column("ageRange", String(20), nullable=False),
    Column("urgencyLevel", String(20), nullable=False),
    Column("recommendedService", String(20), nullable=False),
    Column("summary", Text, nullable=False),
    Column("guidance", JSON, nullable=False),
    Column("warningSignsToWatch", JSON, nullable=False),
    Column("rationale", Text, nullable=False),
    Column("disclaimer", Text, nullable=False),
    Column("reviewDecision", String(20), nullable=True),
    Column("reviewUrgency", String(20), nullable=True),
    Column("reviewHelpful", Boolean, nullable=True),
)

estado = {"motor": None}


def agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def criarMotor(url):
    if url.startswith("sqlite"):
        argumentos = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            argumentos["poolclass"] = StaticPool
        return create_engine(url, **argumentos)
    return create_engine(url, pool_pre_ping=True)


def obterMotor():
    if estado["motor"] is None:
        motor = criarMotor(obterUrlBanco())
        metadados.create_all(motor)
        estado["motor"] = motor
    return estado["motor"]


def reiniciarBanco():
    motor = obterMotor()
    metadados.drop_all(motor)
    metadados.create_all(motor)
