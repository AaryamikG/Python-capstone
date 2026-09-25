import time

from enterprise_rag.llm.gemini_client import GeminiClient
from enterprise_rag.llm.prompts import QUALITATIVE_SYSTEM_INSTRUCTION, build_qualitative_prompt
from enterprise_rag.logging_config import get_logger
from enterprise_rag.schemas import Citation, QualitativeAnswer

logger = get_logger(__name__)

NOT_FOUND_ANSWER = "I couldn't find anything in the knowledge base relevant to that question."


class QualitativeRAGAgent:
    """Retrieves relevant document chunks from Chroma and asks the LLM to answer grounded in them."""

    def __init__(self, llm_client: GeminiClient, collection, top_k: int = 4, min_similarity: float = 0.35):
        self._llm = llm_client
        self._collection = collection
        self._top_k = top_k
        self._min_similarity = min_similarity

    def answer(self, question: str) -> QualitativeAnswer:
        start = time.perf_counter()
        results = self._collection.query(
            query_texts=[question],
            n_results=self._top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        citations: list[Citation] = []
        chunks: list[str] = []
        for doc, meta, distance in zip(documents, metadatas, distances):
            similarity = 1.0 - distance
            if similarity < self._min_similarity:
                continue
            chunk_id = f"{meta['doc_name']}_chunk_{meta['chunk_index']}"
            citations.append(Citation(doc_name=meta["doc_name"], chunk_id=chunk_id, similarity=similarity))
            chunks.append(doc)

        if not chunks:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "qualitative_query_not_found",
                extra={"event_data": {"query": question, "execution_time_ms": elapsed}},
            )
            return QualitativeAnswer(answer=NOT_FOUND_ANSWER, citations=[], found_in_kb=False)

        prompt = build_qualitative_prompt(question, chunks)
        answer_text = self._llm.generate_text(prompt, system_instruction=QUALITATIVE_SYSTEM_INSTRUCTION)

        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "qualitative_query_handled",
            extra={
                "event_data": {
                    "query": question,
                    "retrieved_sources": [c.chunk_id for c in citations],
                    "similarities": [round(c.similarity, 3) for c in citations],
                    "execution_time_ms": elapsed,
                }
            },
        )
        return QualitativeAnswer(answer=answer_text, citations=citations, found_in_kb=True)
