from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response body from the /chat endpoint."""

    reply: str
    escalate: bool
    sources: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    faiss_loaded: bool
    document_count: int
