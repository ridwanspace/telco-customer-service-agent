from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router, set_vector_store
from src.core.config import settings
from src.rag.embeddings import embed_texts
from src.rag.ingestion import load_knowledge_base
from src.rag.vector_store import VectorStore

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _initialize_vector_store() -> VectorStore:
    """Load FAISS index from disk, or ingest knowledge base and create a new one."""
    vs = VectorStore()
    index_path = settings.faiss_index_path

    # Try loading existing index
    try:
        vs.load(index_path)
        logger.info("Loaded FAISS index from %s (%d vectors)", index_path, vs.count)
        return vs
    except FileNotFoundError:
        logger.info("No existing FAISS index found — ingesting knowledge base")

    # Ingest knowledge base
    chunks = load_knowledge_base(settings.knowledge_base_path)
    logger.info("Loaded %d chunks from knowledge base", len(chunks))

    if not chunks:
        logger.warning("No chunks found in knowledge base")
        return vs

    # Generate embeddings
    texts = [c.content for c in chunks]
    embeddings = embed_texts(texts)
    logger.info("Generated %d embeddings", len(embeddings))

    # Add to vector store and persist
    vs.add(chunks, embeddings)
    vs.save(index_path)
    logger.info("Saved FAISS index to %s (%d vectors)", index_path, vs.count)

    return vs


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan — initialize vector store on startup."""
    logger.info("Starting %s", settings.app_name)

    vs = _initialize_vector_store()
    set_vector_store(vs)

    logger.info("Application ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="MyTelco Customer Service AI Agent",
    description=(
        "AI-powered customer service agent for a telecommunications company. "
        "Uses RAG with FAISS and Google Gemini to answer questions about "
        "billing, service plans, and troubleshooting."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
