import chromadb

COLLECTION_NAME = "enterprise_docs"


def get_or_create_collection(persist_path: str, embedding_fn):
    client = chromadb.PersistentClient(path=persist_path)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection(persist_path: str, embedding_fn):
    """Delete-and-recreate, used by the ingestion script so re-runs don't duplicate chunks."""
    client = chromadb.PersistentClient(path=persist_path)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
