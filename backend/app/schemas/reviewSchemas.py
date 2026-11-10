from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.triageSchemas import UrgencyLevel


class ReviewDecision(str, Enum):
    confirmed = "confirmed"
    corrected = "corrected"


class ReviewRequest(BaseModel):
    recordId: str = Field(min_length=1, max_length=64)
    decision: ReviewDecision
    correctedUrgency: UrgencyLevel | None = None
    helpful: bool | None = None


class ReviewResponse(BaseModel):
    recordId: str
    protocol: str
    decision: ReviewDecision
    finalUrgency: UrgencyLevel
    status: str
