from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "telco-customer-service-agent"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    embedding_model: str = "gemini-embedding-001"

    # RAG
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 3
    similarity_threshold: float = 0.3

    # FAISS
    faiss_index_path: str = "data/faiss_index"

    # Knowledge base
    knowledge_base_path: str = "knowledge_base"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
