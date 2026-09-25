from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer


class LocalSTEmbeddingFunction(EmbeddingFunction):
    """Local, free embedding function (no external API calls) backed by sentence-transformers.
    Embeddings are normalized so Chroma's cosine distance maps cleanly to a 0-1 similarity score."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    def __call__(self, input: Documents) -> Embeddings:
        vectors = self._model.encode(list(input), convert_to_numpy=True, normalize_embeddings=True)
        return vectors.tolist()

    @staticmethod
    def name() -> str:
        return "local-sentence-transformers"

    def get_config(self) -> dict:
        return {"model_name": self._model_name}

    @staticmethod
    def build_from_config(config: dict) -> "LocalSTEmbeddingFunction":
        return LocalSTEmbeddingFunction(model_name=config["model_name"])
