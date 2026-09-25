from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Output of the Manager agent's query classifier."""

    type: Literal["qualitative", "quantitative", "complex", "ambiguous"]
    reasoning: str
    clarification_question: str | None = Field(
        default=None, description="Required when type == 'ambiguous'."
    )
    qualitative_sub_query: str | None = Field(
        default=None, description="Populated when type is 'qualitative' or 'complex'."
    )
    quantitative_sub_query: str | None = Field(
        default=None, description="Populated when type is 'quantitative' or 'complex'."
    )


class SqlGenerationResult(BaseModel):
    """Output of the Quantitative agent's NL-to-SQL step."""

    sql: str
    explanation: str


class Citation(BaseModel):
    doc_name: str
    chunk_id: str
    similarity: float

    def format(self) -> str:
        return f"{self.doc_name} (chunk {self.chunk_id.rsplit('_', 1)[-1]}, similarity {self.similarity:.2f})"


class QualitativeAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    found_in_kb: bool = True


class QuantitativeAnswer(BaseModel):
    answer: str
    sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[list] = Field(default_factory=list)
    error: str | None = None


class ManagerAnswer(BaseModel):
    type: Literal["qualitative", "quantitative", "complex", "ambiguous"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    sql: str | None = None
    agents_used: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
