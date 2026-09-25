import time

from enterprise_rag.agents.qualitative_agent import QualitativeRAGAgent
from enterprise_rag.agents.quantitative_agent import QuantitativeSQLAgent
from enterprise_rag.llm.gemini_client import GeminiClient
from enterprise_rag.llm.prompts import (
    CLASSIFIER_SYSTEM_INSTRUCTION,
    SYNTHESIS_SYSTEM_INSTRUCTION,
    build_synthesis_prompt,
)
from enterprise_rag.logging_config import get_logger
from enterprise_rag.schemas import ClassificationResult, ManagerAnswer, QualitativeAnswer, QuantitativeAnswer

logger = get_logger(__name__)


def _format_citations(citations) -> str:
    if not citations:
        return "none"
    return "; ".join(c.format() for c in citations)


class ManagerAgent:
    """Classifies each query, routes it to the qualitative and/or quantitative agent, and merges
    multi-agent answers into one clearly labeled response."""

    def __init__(
        self,
        llm_client: GeminiClient,
        qualitative_agent: QualitativeRAGAgent,
        quantitative_agent: QuantitativeSQLAgent,
    ):
        self._llm = llm_client
        self.qualitative_agent = qualitative_agent
        self.quantitative_agent = quantitative_agent

    def classify(self, query: str) -> ClassificationResult:
        return self._llm.generate_json(
            query, ClassificationResult, system_instruction=CLASSIFIER_SYSTEM_INSTRUCTION
        )

    def handle_query(self, query: str) -> ManagerAnswer:
        start = time.perf_counter()
        classification = self.classify(query)

        if classification.type == "ambiguous":
            answer = self._handle_ambiguous(classification)
        elif classification.type == "qualitative":
            answer = self._handle_qualitative(classification, query)
        elif classification.type == "quantitative":
            answer = self._handle_quantitative(classification, query)
        else:
            answer = self._handle_complex(classification, query)

        answer.execution_time_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "manager_query_handled",
            extra={
                "event_data": {
                    "query": query,
                    "classification": classification.type,
                    "agents_used": answer.agents_used,
                    "execution_time_ms": answer.execution_time_ms,
                }
            },
        )
        return answer

    @staticmethod
    def _handle_ambiguous(classification: ClassificationResult) -> ManagerAnswer:
        question = classification.clarification_question or "Could you clarify your question?"
        return ManagerAnswer(type="ambiguous", answer=question, agents_used=[])

    def _handle_qualitative(self, classification: ClassificationResult, query: str) -> ManagerAnswer:
        result: QualitativeAnswer = self.qualitative_agent.answer(classification.qualitative_sub_query or query)
        return ManagerAnswer(
            type="qualitative",
            answer=result.answer,
            citations=result.citations,
            agents_used=["qualitative"],
        )

    def _handle_quantitative(self, classification: ClassificationResult, query: str) -> ManagerAnswer:
        result: QuantitativeAnswer = self.quantitative_agent.answer(classification.quantitative_sub_query or query)
        return ManagerAnswer(
            type="quantitative",
            answer=result.answer,
            sql=result.sql,
            agents_used=["quantitative"],
        )

    def _handle_complex(self, classification: ClassificationResult, query: str) -> ManagerAnswer:
        qual: QualitativeAnswer = self.qualitative_agent.answer(classification.qualitative_sub_query or query)
        quant: QuantitativeAnswer = self.quantitative_agent.answer(classification.quantitative_sub_query or query)

        synthesis_prompt = build_synthesis_prompt(query, qual.answer, quant.answer)
        synthesis = self._llm.generate_text(synthesis_prompt, system_instruction=SYNTHESIS_SYSTEM_INSTRUCTION)

        merged = (
            "## Qualitative Findings (handled by Qualitative RAG Agent)\n"
            f"{qual.answer}\n\nSources: {_format_citations(qual.citations)}\n\n"
            "## Quantitative Findings (handled by Quantitative SQL Agent)\n"
            f"{quant.answer}\n\nSQL: {quant.sql or 'n/a'}\n\n"
            "## Combined Analysis\n"
            f"{synthesis}"
        )
        return ManagerAnswer(
            type="complex",
            answer=merged,
            citations=qual.citations,
            sql=quant.sql,
            agents_used=["qualitative", "quantitative"],
        )
