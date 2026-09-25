"""Sanity checks that the generated data artifacts and client constructors work, without making
any real Gemini API calls (object construction only)."""

import sqlite3
from pathlib import Path

import pytest

from enterprise_rag.config import Settings
from enterprise_rag.llm.gemini_client import GeminiClient
from enterprise_rag.vectorstore.embedding_function import LocalSTEmbeddingFunction
from enterprise_rag.vectorstore.store import get_or_create_collection

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.skipif(not (ROOT / "data" / "enterprise.db").exists(), reason="run scripts/generate_sql_data.py first")
def test_sqlite_database_is_reachable():
    conn = sqlite3.connect(ROOT / "data" / "enterprise.db")
    try:
        assert conn.execute("SELECT 1").fetchone() == (1,)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"customers", "sales", "churn_events", "employee_satisfaction_scores", "regions"} <= tables
    finally:
        conn.close()


@pytest.mark.skipif(not (ROOT / "data" / "chroma").exists(), reason="run scripts/build_vector_store.py first")
def test_chroma_collection_is_reachable(embedding_fn):
    collection = get_or_create_collection(str(ROOT / "data" / "chroma"), embedding_fn)
    assert collection.count() > 0


def test_gemini_client_constructs_with_api_key():
    client = GeminiClient(api_key="dummy-key-for-construction-only")
    assert client is not None


def test_gemini_client_rejects_missing_api_key():
    with pytest.raises(ValueError):
        GeminiClient(api_key="")


def test_settings_reads_defaults_without_a_real_env_file(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    settings = Settings(_env_file=None)
    assert settings.gemini_model == "gemini-3.5-flash-lite"
    assert settings.top_k == 4
