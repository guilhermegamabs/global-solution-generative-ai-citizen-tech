from pydantic import BaseModel

from app.schemas.reviewSchemas import ReviewDecision
from app.schemas.triageSchemas import TriageResponse, UrgencyLevel


class ReviewSummary(BaseModel):
    decision: ReviewDecision
    finalUrgency: UrgencyLevel
    helpful: bool | None = None


class HistoryItem(TriageResponse):
    review: ReviewSummary | None = None


class HistoryResponse(BaseModel):
    records: list[HistoryItem]
