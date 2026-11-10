from typing import Annotated

from pydantic import BaseModel, StringConstraints

Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]

NovaSenha = Annotated[str, StringConstraints(min_length=8, max_length=128)]

SenhaInformada = Annotated[str, StringConstraints(min_length=1, max_length=128)]

CodigoSeisDigitos = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]


class RegisterRequest(BaseModel):
    email: Email
    password: NovaSenha


class VerifyRequest(BaseModel):
    email: Email
    code: CodigoSeisDigitos


class ResendRequest(BaseModel):
    email: Email


class LoginRequest(BaseModel):
    email: Email
    password: SenhaInformada


class SessionResponse(BaseModel):
    token: str
    email: str


class MessageResponse(BaseModel):
    message: str


class MeResponse(BaseModel):
    email: str
