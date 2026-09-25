"""Chunks data/documents/*.md and indexes them into the local Chroma collection.

Idempotent: deletes and recreates the collection each run. Run with:
    python scripts/build_vector_store.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from enterprise_rag.config import Settings  # noqa: E402
from enterprise_rag.vectorstore.chunking import chunk_text  # noqa: E402
from enterprise_rag.vectorstore.embedding_function import LocalSTEmbeddingFunction  # noqa: E402
from enterprise_rag.vectorstore.store import reset_collection  # noqa: E402

DOCUMENTS_DIR = ROOT / "data" / "documents"


def main() -> None:
    settings = Settings()
    embedding_fn = LocalSTEmbeddingFunction(settings.embedding_model)
    collection = reset_collection(settings.chroma_path, embedding_fn)

    ids, documents, metadatas = [], [], []
    for doc_path in sorted(DOCUMENTS_DIR.glob("*.md")):
        text = doc_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for chunk_index, chunk in enumerate(chunks):
            ids.append(f"{doc_path.name}_chunk_{chunk_index}")
            documents.append(chunk)
            metadatas.append(
                {
                    "doc_name": doc_path.name,
                    "source_path": str(doc_path.relative_to(ROOT)),
                    "chunk_index": chunk_index,
                }
            )

    if not ids:
        print(f"No documents found in {DOCUMENTS_DIR}")
        return

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Indexed {len(ids)} chunks from {len(list(DOCUMENTS_DIR.glob('*.md')))} documents into "
          f"{settings.chroma_path}")


if __name__ == "__main__":
    main()
