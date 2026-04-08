from __future__ import annotations

import logging

from google import genai
from google.genai.types import Content, GenerateContentConfig, Part

from src.api.schemas import ChatResponse, Message
from src.core.config import settings
from src.core.prompts import ESCALATE_PREFIX, NO_CONTEXT_RESPONSE, SYSTEM_PROMPT
from src.rag.retriever import (
    RetrievalResult,
    format_context,
    get_source_documents,
    retrieve,
)
from src.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

MAX_HISTORY_MESSAGES = 10


def _get_client() -> genai.Client:
    """Get or create the Gemini client (singleton)."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _build_contents(
    user_message: str,
    conversation_history: list[Message],
) -> list[Content]:
    """Build the Gemini contents array from conversation history and current message."""
    contents: list[Content] = []

    # Add recent conversation history (limit to avoid exceeding context window)
    recent_history = conversation_history[-MAX_HISTORY_MESSAGES:]
    for msg in recent_history:
        role = "user" if msg.role == "user" else "model"
        contents.append(Content(role=role, parts=[Part(text=msg.content)]))

    # Add current user message
    contents.append(Content(role="user", parts=[Part(text=user_message)]))

    return contents


def _detect_escalation(reply: str) -> tuple[str, bool]:
    """Detect if the LLM response indicates escalation. Returns (cleaned reply, escalate flag)."""
    if reply.strip().upper().startswith(ESCALATE_PREFIX.upper()):
        cleaned = reply.strip()[len(ESCALATE_PREFIX) :].strip()
        return cleaned, True

    escalation_phrases = [
        "connect you with a human agent",
        "transfer you to a human",
        "let me connect you",
        "escalate this",
        "human agent who can help",
        "i don't have enough information",
        "i cannot help with",
        "beyond my ability",
    ]
    reply_lower = reply.lower()
    for phrase in escalation_phrases:
        if phrase in reply_lower:
            return reply, True

    return reply, False


def chat(
    user_message: str,
    conversation_history: list[Message],
    vector_store: VectorStore,
) -> ChatResponse:
    """Process a user message through the RAG pipeline and return a response."""
    # Step 1: Retrieve relevant chunks
    retrieval_results: list[RetrievalResult] = retrieve(user_message, vector_store)
    sources = get_source_documents(retrieval_results)

    logger.info(
        "Retrieved %d chunks for query: %s",
        len(retrieval_results),
        user_message[:50],
    )

    # Step 2: If no relevant chunks, escalate immediately
    if not retrieval_results:
        logger.info("No relevant chunks found — escalating")
        return ChatResponse(
            reply=NO_CONTEXT_RESPONSE,
            escalate=True,
            sources=[],
        )

    # Step 3: Build prompt with context
    context = format_context(retrieval_results)
    system_prompt = SYSTEM_PROMPT.format(context=context)

    # Step 4: Build conversation contents
    contents = _build_contents(user_message, conversation_history)

    # Step 5: Call Gemini
    client = _get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=1024,
            system_instruction=system_prompt,
        ),
    )

    reply_text = response.text or NO_CONTEXT_RESPONSE

    # Step 6: Detect escalation in response
    reply_text, escalate = _detect_escalation(reply_text)

    logger.info("Response escalate=%s, sources=%s", escalate, sources)

    return ChatResponse(
        reply=reply_text,
        escalate=escalate,
        sources=sources,
    )
