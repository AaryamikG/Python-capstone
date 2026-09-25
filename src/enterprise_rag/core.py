from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.agents.qualitative_agent import QualitativeRAGAgent
from enterprise_rag.agents.quantitative_agent import QuantitativeSQLAgent
from enterprise_rag.config import Settings
from enterprise_rag.llm.gemini_client import GeminiClient
from enterprise_rag.vectorstore.embedding_function import LocalSTEmbeddingFunction
from enterprise_rag.vectorstore.store import get_or_create_collection


def build_manager_agent(settings: Settings) -> ManagerAgent:
    """Single factory used by both the CLI and the API so agent wiring never diverges."""
    llm_client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)

    embedding_fn = LocalSTEmbeddingFunction(settings.embedding_model)
    collection = get_or_create_collection(settings.chroma_path, embedding_fn)

    qualitative_agent = QualitativeRAGAgent(
        llm_client=llm_client,
        collection=collection,
        top_k=settings.top_k,
        min_similarity=settings.min_similarity,
    )
    quantitative_agent = QuantitativeSQLAgent(llm_client=llm_client, sqlite_path=settings.sqlite_path)

    return ManagerAgent(
        llm_client=llm_client,
        qualitative_agent=qualitative_agent,
        quantitative_agent=quantitative_agent,
    )
