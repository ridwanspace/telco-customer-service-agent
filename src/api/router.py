from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.agent.service import chat
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.rag.vector_store import VectorStore

router = APIRouter()

# Global vector store — initialized during app lifespan
_vector_store: VectorStore | None = None


def set_vector_store(vs: VectorStore) -> None:
    """Set the global vector store (called during app startup)."""
    global _vector_store
    _vector_store = vs


def get_vector_store() -> VectorStore:
    """Get the global vector store."""
    if _vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    return _vector_store


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Chat with the Telco customer service AI agent."""
    vs = get_vector_store()
    return chat(
        user_message=request.message,
        conversation_history=request.conversation_history,
        vector_store=vs,
    )


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    if _vector_store is None:
        return HealthResponse(
            status="unhealthy",
            faiss_loaded=False,
            document_count=0,
        )
    return HealthResponse(
        status="healthy",
        faiss_loaded=True,
        document_count=_vector_store.count,
    )
