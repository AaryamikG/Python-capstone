from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration, shared by the CLI and the API. Reads from .env / process env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_path: str = "data/chroma"
    sqlite_path: str = "data/enterprise.db"
    top_k: int = 4
    min_similarity: float = 0.35
    log_level: str = "INFO"
