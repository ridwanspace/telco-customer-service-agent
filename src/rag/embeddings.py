from __future__ import annotations

from google import genai

from src.core.config import settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client (singleton)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Generate embeddings for a list of texts using Gemini text-embedding-004."""
    client = _get_client()
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config={"task_type": task_type},
    )
    return [list(e.values) for e in result.embeddings]


def embed_query(query: str) -> list[float]:
    """Embed a single query for retrieval search."""
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
