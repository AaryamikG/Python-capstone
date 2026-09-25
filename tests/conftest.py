import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from enterprise_rag.vectorstore.chunking import chunk_text  # noqa: E402
from enterprise_rag.vectorstore.embedding_function import LocalSTEmbeddingFunction  # noqa: E402
from enterprise_rag.vectorstore.store import get_or_create_collection  # noqa: E402

DOCUMENTS_DIR = ROOT / "data" / "documents"


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """Every test gets a dummy key so Settings()/GeminiClient() construction never fails and no
    test can accidentally reach the real (free-tier) Gemini API."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-used")


@pytest.fixture(scope="session")
def embedding_fn():
    # Loaded once per test session — it's a local model, no network/API cost, just slow to load.
    return LocalSTEmbeddingFunction()


@pytest.fixture
def tmp_chroma_collection(tmp_path, embedding_fn):
    collection = get_or_create_collection(str(tmp_path / "chroma"), embedding_fn)
    collection.add(
        ids=["security_policy.md_chunk_0", "security_policy.md_chunk_1", "code_review_process.md_chunk_0"],
        documents=[
            "All company data is classified into Public, Internal, Confidential, and Restricted tiers.",
            "Passwords must be at least 14 characters and are rotated every 180 days.",
            "Every pull request requires a minimum of two reviewer approvals before it can merge.",
        ],
        metadatas=[
            {"doc_name": "security_policy.md", "source_path": "data/documents/security_policy.md", "chunk_index": 0},
            {"doc_name": "security_policy.md", "source_path": "data/documents/security_policy.md", "chunk_index": 1},
            {
                "doc_name": "code_review_process.md",
                "source_path": "data/documents/code_review_process.md",
                "chunk_index": 0,
            },
        ],
    )
    return collection


@pytest.fixture(scope="session")
def full_corpus_collection(tmp_path_factory, embedding_fn):
    """Indexes the real data/documents/*.md corpus into a session-scoped temp Chroma collection,
    for the retrieval-quality eval - real documents, real embeddings, still zero API cost."""
    persist_path = str(tmp_path_factory.mktemp("chroma_full_corpus"))
    collection = get_or_create_collection(persist_path, embedding_fn)

    ids, documents, metadatas = [], [], []
    for doc_path in sorted(DOCUMENTS_DIR.glob("*.md")):
        for chunk_index, chunk in enumerate(chunk_text(doc_path.read_text(encoding="utf-8"))):
            ids.append(f"{doc_path.name}_chunk_{chunk_index}")
            documents.append(chunk)
            metadatas.append({"doc_name": doc_path.name, "chunk_index": chunk_index})
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return collection


@pytest.fixture
def tmp_sqlite_path(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE sales (sale_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, amount REAL NOT NULL);
        INSERT INTO customers (customer_id, name, status) VALUES (1, 'Acme Co', 'active'), (2, 'Globex', 'churned');
        INSERT INTO sales (sale_id, customer_id, amount) VALUES (1, 1, 100.0), (2, 1, 250.0), (3, 2, 75.0);
        """
    )
    conn.commit()
    conn.close()
    return str(db_path)
