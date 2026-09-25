from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural-language question for the assistant.")


class CitationOut(BaseModel):
    doc_name: str
    chunk_id: str
    similarity: float


class QueryResponse(BaseModel):
    type: Literal["qualitative", "quantitative", "complex", "ambiguous"]
    answer: str
    citations: list[CitationOut] = Field(default_factory=list)
    sql: str | None = None
    agents_used: list[str] = Field(default_factory=list)
    execution_time_ms: float


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    gemini_configured: bool
    chroma_available: bool
    sqlite_available: bool
