from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class AgeRange(str, Enum):
    child = "child"
    teen = "teen"
    adult = "adult"
    senior = "senior"


class Duration(str, Enum):
    lessThanDay = "lessThanDay"
    oneToThreeDays = "oneToThreeDays"
    fourToSevenDays = "fourToSevenDays"
    moreThanWeek = "moreThanWeek"


class WarningSign(str, Enum):
    chestPain = "chestPain"
    breathingDifficulty = "breathingDifficulty"
    lossOfConsciousness = "lossOfConsciousness"
    severeBleeding = "severeBleeding"
    confusion = "confusion"
    strokeSigns = "strokeSigns"
    highFever = "highFever"


class UrgencyLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    emergency = "emergency"


class RecommendedService(str, Enum):
    selfCare = "selfCare"
    basicUnit = "basicUnit"
    urgentCare = "urgentCare"
    ambulance = "ambulance"


class TriageRequest(BaseModel):
    symptoms: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=10, max_length=800)
    ]
    ageRange: AgeRange
    duration: Duration
    warningSigns: list[WarningSign] = Field(default_factory=list, max_length=7)
    hasChronicCondition: bool = False


class TriageModelOutput(BaseModel):
    urgencyLevel: UrgencyLevel
    recommendedService: RecommendedService
    summary: str = Field(min_length=1, max_length=400)
    guidance: list[str] = Field(min_length=1, max_length=6)
    warningSignsToWatch: list[str] = Field(max_length=6)
    rationale: str = Field(min_length=1, max_length=800)


class TriageResponse(TriageModelOutput):
    recordId: str
    protocol: str
    createdAt: datetime
    ageRange: AgeRange
    disclaimer: str
