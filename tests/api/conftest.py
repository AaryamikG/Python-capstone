import pytest
from fastapi.testclient import TestClient

from enterprise_rag.api.deps import get_manager_agent
from enterprise_rag.api.main import app
from enterprise_rag.schemas import (
    ClassificationResult,
    QualitativeAnswer,
    QuantitativeAnswer,
    ManagerAnswer,
    Citation,
)


class _FakeSubAgent:
    def __init__(self, response):
        self._response = response
        self.queries: list[str] = []

    def answer(self, query: str):
        self.queries.append(query)
        return self._response


class FakeManagerAgent:
    def __init__(self):
        self.qualitative_agent = _FakeSubAgent(
            QualitativeAnswer(
                answer="Passwords must be 14+ characters.",
                citations=[Citation(doc_name="security_policy.md", chunk_id="security_policy.md_chunk_1", similarity=0.62)],
            )
        )
        self.quantitative_agent = _FakeSubAgent(
            QuantitativeAnswer(answer="churn_rate: 0.2", sql="SELECT 1", columns=["churn_rate"], rows=[[0.2]])
        )
        self.handle_query_calls: list[str] = []
        self.classify_calls: list[str] = []

    def handle_query(self, query: str) -> ManagerAnswer:
        self.handle_query_calls.append(query)
        return ManagerAnswer(
            type="qualitative",
            answer="Passwords must be 14+ characters.",
            citations=self.qualitative_agent._response.citations,
            agents_used=["qualitative"],
            execution_time_ms=12.5,
        )

    def classify(self, query: str) -> ClassificationResult:
        self.classify_calls.append(query)
        return ClassificationResult(type="qualitative", reasoning="policy question", qualitative_sub_query=query)


@pytest.fixture
def fake_manager():
    return FakeManagerAgent()


@pytest.fixture
def client(fake_manager):
    app.dependency_overrides[get_manager_agent] = lambda: fake_manager
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
