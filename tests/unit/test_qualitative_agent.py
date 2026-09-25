from enterprise_rag.agents.qualitative_agent import NOT_FOUND_ANSWER, QualitativeRAGAgent

from tests.fixtures.fake_gemini_client import FakeGeminiClient


def test_relevant_query_returns_answer_with_citations(tmp_chroma_collection):
    fake_llm = FakeGeminiClient(text_responses=["Passwords must be 14+ characters and rotated every 180 days."])
    agent = QualitativeRAGAgent(llm_client=fake_llm, collection=tmp_chroma_collection, top_k=3, min_similarity=0.2)

    result = agent.answer("What are the password requirements?")

    assert result.found_in_kb is True
    assert result.answer == "Passwords must be 14+ characters and rotated every 180 days."
    assert result.citations, "expected at least one citation"
    assert result.citations[0].doc_name == "security_policy.md"
    assert 0.0 <= result.citations[0].similarity <= 1.0
    assert len(fake_llm.text_calls) == 1


def test_unrelated_query_returns_not_found_without_calling_llm(tmp_chroma_collection):
    fake_llm = FakeGeminiClient()
    agent = QualitativeRAGAgent(llm_client=fake_llm, collection=tmp_chroma_collection, top_k=3, min_similarity=0.8)

    result = agent.answer("What is the weather like on Mars today?")

    assert result.found_in_kb is False
    assert result.answer == NOT_FOUND_ANSWER
    assert result.citations == []
    assert fake_llm.text_calls == []  # never spends an LLM call on a query with no relevant chunks
