from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class UnitsRequest(BaseModel):
    cep: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{5}-?\d{3}$")]
    limit: int = Field(default=5, ge=1, le=10)


class NearbyUnit(BaseModel):
    name: str
    address: str
    neighborhood: str
    phone: str | None = None
    latitude: float
    longitude: float
    open24h: bool
    distanceKm: float
    positionUncertain: bool = False


class UnitsOrigin(BaseModel):
    latitude: float
    longitude: float
    city: str
    state: str
    neighborhood: str
    approximate: bool = False


class UnitsResponse(BaseModel):
    origin: UnitsOrigin
    units: list[NearbyUnit]
