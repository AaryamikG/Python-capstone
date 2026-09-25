from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.schemas import ClassificationResult, QualitativeAnswer, QuantitativeAnswer

from tests.fixtures.fake_gemini_client import FakeGeminiClient


class FakeSubAgent:
    def __init__(self, response):
        self._response = response
        self.calls: list[str] = []

    def answer(self, query: str):
        self.calls.append(query)
        return self._response


def test_qualitative_classification_only_calls_qualitative_agent():
    fake_llm = FakeGeminiClient(
        json_responses=[
            ClassificationResult(
                type="qualitative", reasoning="policy question", qualitative_sub_query="security policy?"
            )
        ]
    )
    qual = FakeSubAgent(QualitativeAnswer(answer="policy answer", citations=[]))
    quant = FakeSubAgent(QuantitativeAnswer(answer="unused"))
    manager = ManagerAgent(llm_client=fake_llm, qualitative_agent=qual, quantitative_agent=quant)

    result = manager.handle_query("What is our security policy?")

    assert result.type == "qualitative"
    assert result.answer == "policy answer"
    assert result.agents_used == ["qualitative"]
    assert qual.calls == ["security policy?"]
    assert quant.calls == []


def test_quantitative_classification_only_calls_quantitative_agent():
    fake_llm = FakeGeminiClient(
        json_responses=[
            ClassificationResult(
                type="quantitative", reasoning="data question", quantitative_sub_query="churn rate?"
            )
        ]
    )
    qual = FakeSubAgent(QualitativeAnswer(answer="unused"))
    quant = FakeSubAgent(QuantitativeAnswer(answer="12% churn", sql="SELECT 1"))
    manager = ManagerAgent(llm_client=fake_llm, qualitative_agent=qual, quantitative_agent=quant)

    result = manager.handle_query("What's our churn rate?")

    assert result.type == "quantitative"
    assert result.answer == "12% churn"
    assert result.sql == "SELECT 1"
    assert result.agents_used == ["quantitative"]
    assert qual.calls == []
    assert quant.calls == ["churn rate?"]


def test_ambiguous_classification_never_calls_sub_agents():
    fake_llm = FakeGeminiClient(
        json_responses=[
            ClassificationResult(
                type="ambiguous", reasoning="too vague", clarification_question="Which product do you mean?"
            )
        ]
    )
    qual = FakeSubAgent(QualitativeAnswer(answer="unused"))
    quant = FakeSubAgent(QuantitativeAnswer(answer="unused"))
    manager = ManagerAgent(llm_client=fake_llm, qualitative_agent=qual, quantitative_agent=quant)

    result = manager.handle_query("Tell me about it")

    assert result.type == "ambiguous"
    assert result.answer == "Which product do you mean?"
    assert result.agents_used == []
    assert qual.calls == []
    assert quant.calls == []


def test_complex_classification_calls_both_and_merges_with_labeled_sections():
    fake_llm = FakeGeminiClient(
        json_responses=[
            ClassificationResult(
                type="complex",
                reasoning="needs both",
                qualitative_sub_query="satisfaction policy?",
                quantitative_sub_query="satisfaction scores?",
            )
        ],
        text_responses=["Scores are below benchmark, consistent with the survey policy gap noted."],
    )
    qual = FakeSubAgent(QualitativeAnswer(answer="Quarterly satisfaction surveys are benchmarked.", citations=[]))
    quant = FakeSubAgent(QuantitativeAnswer(answer="Engineering avg 6.5 vs benchmark 7.5", sql="SELECT 1"))
    manager = ManagerAgent(llm_client=fake_llm, qualitative_agent=qual, quantitative_agent=quant)

    result = manager.handle_query("How does satisfaction compare to industry standards?")

    assert result.type == "complex"
    assert result.agents_used == ["qualitative", "quantitative"]
    assert "## Qualitative Findings" in result.answer
    assert "## Quantitative Findings" in result.answer
    assert "## Combined Analysis" in result.answer
    assert qual.calls == ["satisfaction policy?"]
    assert quant.calls == ["satisfaction scores?"]
