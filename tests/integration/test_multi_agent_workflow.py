"""End-to-end multi-agent flow using the real Qualitative/Quantitative agents (real Chroma + real
SQLite) but a FakeGeminiClient standing in for Gemini - no real API calls."""

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.agents.qualitative_agent import QualitativeRAGAgent
from enterprise_rag.agents.quantitative_agent import QuantitativeSQLAgent
from enterprise_rag.schemas import ClassificationResult, SqlGenerationResult

from tests.fixtures.fake_gemini_client import FakeGeminiClient


def test_complex_query_merges_real_qualitative_and_quantitative_agents(tmp_chroma_collection, tmp_sqlite_path):
    fake_llm = FakeGeminiClient(
        json_responses=[
            ClassificationResult(
                type="complex",
                reasoning="needs both docs and data",
                qualitative_sub_query="What are the password requirements?",
                quantitative_sub_query="How many customers do we have?",
            ),
            SqlGenerationResult(sql="SELECT COUNT(*) AS total FROM customers", explanation="count customers"),
        ],
        text_responses=[
            "Passwords must be at least 14 characters, rotated every 180 days.",
            "We have 2 customers, and password policy is unrelated to that count.",
        ],
    )
    qual_agent = QualitativeRAGAgent(llm_client=fake_llm, collection=tmp_chroma_collection, min_similarity=0.2)
    quant_agent = QuantitativeSQLAgent(llm_client=fake_llm, sqlite_path=tmp_sqlite_path)
    manager = ManagerAgent(llm_client=fake_llm, qualitative_agent=qual_agent, quantitative_agent=quant_agent)

    result = manager.handle_query(
        "What are our password requirements and how many customers do we have?"
    )

    assert result.type == "complex"
    assert result.agents_used == ["qualitative", "quantitative"]
    assert "## Qualitative Findings" in result.answer
    assert "## Quantitative Findings" in result.answer
    assert "## Combined Analysis" in result.answer
    assert "password" in result.answer.lower()
    assert result.sql == "SELECT COUNT(*) AS total FROM customers"
    assert result.citations, "expected the qualitative half to produce citations"
