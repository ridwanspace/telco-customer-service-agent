from __future__ import annotations

from dataclasses import dataclass

from src.core.config import settings
from src.rag.embeddings import embed_query
from src.rag.ingestion import Chunk
from src.rag.vector_store import VectorStore


@dataclass
class RetrievalResult:
    """A single retrieval result with chunk content and similarity score."""

    chunk: Chunk
    score: float


def retrieve(
    query: str,
    vector_store: VectorStore,
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[RetrievalResult]:
    """Retrieve relevant chunks for a query from the vector store."""
    top_k = top_k or settings.top_k_results
    threshold = threshold or settings.similarity_threshold

    query_embedding = embed_query(query)
    results = vector_store.search(query_embedding, top_k=top_k, threshold=threshold)

    return [RetrievalResult(chunk=chunk, score=score) for chunk, score in results]


def format_context(results: list[RetrievalResult]) -> str:
    """Format retrieval results into a context string for the LLM prompt."""
    if not results:
        return "No relevant information found in the knowledge base."

    context_parts: list[str] = []
    for r in results:
        context_parts.append(f"- {r.chunk.content}")

    return "\n".join(context_parts)


def get_source_documents(results: list[RetrievalResult]) -> list[str]:
    """Extract unique source document names from retrieval results."""
    seen: set[str] = set()
    sources: list[str] = []
    for r in results:
        if r.chunk.source not in seen:
            seen.add(r.chunk.source)
            sources.append(r.chunk.source)
    return sources
