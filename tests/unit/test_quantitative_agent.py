from enterprise_rag.agents.quantitative_agent import QuantitativeSQLAgent
from enterprise_rag.schemas import SqlGenerationResult

from tests.fixtures.fake_gemini_client import FakeGeminiClient


def test_valid_sql_executes_and_summarizes(tmp_sqlite_path):
    fake_llm = FakeGeminiClient(
        json_responses=[SqlGenerationResult(sql="SELECT name, status FROM customers", explanation="lists customers")]
    )
    agent = QuantitativeSQLAgent(llm_client=fake_llm, sqlite_path=tmp_sqlite_path)

    result = agent.answer("List all customers and their status")

    assert result.error is None
    assert result.sql == "SELECT name, status FROM customers"
    assert result.columns == ["name", "status"]
    assert len(result.rows) == 2
    assert "Acme Co" in result.answer


def test_invalid_sql_is_rejected_before_execution(tmp_sqlite_path):
    fake_llm = FakeGeminiClient(json_responses=[SqlGenerationResult(sql="DROP TABLE customers", explanation="x")])
    agent = QuantitativeSQLAgent(llm_client=fake_llm, sqlite_path=tmp_sqlite_path)

    result = agent.answer("Delete all customers")

    assert result.error is not None
    assert "safe query" in result.answer
    # No SQL execution retry happens on validation failure - the LLM was only called once.
    assert len(fake_llm.json_calls) == 1


def test_execution_failure_retries_once_then_succeeds(tmp_sqlite_path):
    fake_llm = FakeGeminiClient(
        json_responses=[
            SqlGenerationResult(sql="SELECT nonexistent_column FROM customers", explanation="broken"),
            SqlGenerationResult(sql="SELECT name FROM customers", explanation="fixed"),
        ]
    )
    agent = QuantitativeSQLAgent(llm_client=fake_llm, sqlite_path=tmp_sqlite_path)

    result = agent.answer("Show customer names")

    assert result.error is None
    assert result.sql == "SELECT name FROM customers"
    assert len(fake_llm.json_calls) == 2


def test_execution_failure_gives_up_after_one_retry(tmp_sqlite_path):
    fake_llm = FakeGeminiClient(
        json_responses=[
            SqlGenerationResult(sql="SELECT nonexistent_column FROM customers", explanation="broken"),
            SqlGenerationResult(sql="SELECT another_bad_column FROM customers", explanation="still broken"),
        ]
    )
    agent = QuantitativeSQLAgent(llm_client=fake_llm, sqlite_path=tmp_sqlite_path)

    result = agent.answer("Show customer names")

    assert result.error is not None
    assert "couldn't translate" in result.answer
    # Exactly one retry - never a third attempt, to protect free-tier API quota.
    assert len(fake_llm.json_calls) == 2
