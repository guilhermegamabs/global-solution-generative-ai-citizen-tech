from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class AnswerStatus(str, Enum):
    answered = "answered"
    abstained = "abstained"
    outOfScope = "outOfScope"
    blocked = "blocked"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class AssistantRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=500)]
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)
    topic: str | None = Field(default=None, max_length=40)


class SourceItem(BaseModel):
    number: int
    chunkId: str
    title: str
    section: str
    url: str
    accessedAt: str
    excerpt: str
    score: float


class Diagnostics(BaseModel):
    searchQuery: str
    topScore: float
    support: float | None
    retriever: str
    chunking: str
    model: str
    latencyMs: int


class AssistantModelOutput(BaseModel):
    resposta: str = Field(default="", max_length=3000)
    fontesUsadas: list[int] = Field(default_factory=list, max_length=10)
    semEvidencia: bool = False
    foraDoEscopo: bool = False


class AssistantResponse(BaseModel):
    answer: str
    status: AnswerStatus
    confidence: Confidence
    sources: list[SourceItem]
    emergencyNotice: str | None
    alerts: list[str]
    diagnostics: Diagnostics
    disclaimer: str


class TopicsResponse(BaseModel):
    topics: list[str]
