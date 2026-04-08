# Phase 1: Q1 — Build a Customer Service AI Agent

**Created**: 2026-04-08
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL (P0 — 50% of total score)
**Status**: ✅ COMPLETED (2026-04-08)
**Depends On**: Phase 0 (Project Setup)
**Blocks**: Nothing (Q2 is independent)
**Assignment Ref**: Q1 — Build a Customer Service AI Agent (50 pts)

---

## Overview

Build a working AI agent exposed as a FastAPI `/chat` endpoint. The agent answers
Telco customer questions using a RAG pipeline backed by FAISS and Google Gemini.
When it cannot answer confidently, it sets `escalate: true`.

**Scoring breakdown**:
| Criteria | Points |
|----------|--------|
| System prompt quality & role enforcement | 10 pts |
| RAG pipeline — chunking & embedding strategy | 15 pts |
| Retrieval integration & context passing to LLM | 15 pts |
| Fallback & escalation handling | 10 pts |
| **Total** | **50 pts** |

---

## Part 1A — Conversational Endpoint

### Task A1: Request/Response Schemas (`src/api/schemas.py`)

```python
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: list[Message] = []

class ChatResponse(BaseModel):
    reply: str
    escalate: bool
    sources: list[str] = []  # Which KB documents were used
```

**Design decisions**:
- `conversation_history` as a flat list of messages — simple, stateless API
- `sources` field added for transparency (shows which docs informed the answer)
- No session management on the server — client owns conversation state

---

### Task A2: Settings Configuration (`src/core/config.py`)

```python
class Settings(BaseSettings):
    # App
    app_name: str = "telco-customer-service-agent"
    environment: str = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-3-flash-preview"
    embedding_model: str = "gemini-embedding-001"

    # RAG
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 3
    similarity_threshold: float = 0.3

    # FAISS
    faiss_index_path: str = "data/faiss_index"

    model_config = SettingsConfigDict(env_file=".env")
```

---

### Task A3: System Prompt Design (`src/core/prompts.py`)

**System prompt strategy** (scoring: 10 pts):

```
You are a customer service assistant for MyTelco, an Indonesian telecommunications
company. Your role is to help customers with questions about billing, service plans,
and basic troubleshooting.

RULES:
1. ONLY answer using the provided context from the knowledge base. Do not use
   information from outside the context.
2. If the context does not contain enough information to answer the question,
   respond with: "I'm sorry, I don't have enough information to answer that
   question. Let me connect you with a human agent who can help."
   and set escalate to true.
3. Be polite, concise, and professional. Use simple language.
4. When quoting prices, always include the currency (IDR).
5. If the customer is frustrated or the issue is complex, offer to escalate
   to a human agent.
6. Do not make up or guess information — especially about pricing, policies,
   or procedures.
7. For troubleshooting, provide step-by-step guidance from the knowledge base.

CONTEXT FROM KNOWLEDGE BASE:
{context}
```

**Why this structure**:
- **Role definition first** — grounds the model in the correct persona
- **Explicit "ONLY answer using context" rule** — prevents hallucination (critical for billing/pricing)
- **Clear escalation trigger** — defines exact behavior when context is insufficient
- **Currency reminder** — Indonesian Rupiah can be confused with other currencies
- **Frustration detection** — real CS agents escalate emotional situations
- **Context injection at the end** — keeps retrieved docs close to where the model generates

---

### Task A4: FastAPI App & Router (`src/main.py`, `src/api/router.py`)

**Endpoint**: `POST /chat`

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Retrieve relevant chunks from FAISS
    # 2. Build prompt with context
    # 3. Call Gemini
    # 4. Parse response for escalation signals
    # 5. Return structured response
```

**Additional endpoints**:
- `GET /health` — health check (FAISS index loaded, Gemini API reachable)
- `POST /ingest` — trigger knowledge base re-ingestion (optional, for demo)

**App lifespan**:
- On startup: load FAISS index (or ingest if not exists)
- On shutdown: cleanup

---

## Part 1B — RAG Pipeline

### Task B1: Document Ingestion (`src/rag/ingestion.py`)

**Chunking strategy** (scoring: 15 pts):

**Approach**: Semantic chunking by document section with fixed-size fallback.

Since our knowledge base is small (3 documents, ~20 bullet points total), we use
a **per-bullet-point chunking strategy**:

1. **Split by bullet point** — each bullet is a self-contained fact
2. **Prepend document title** as metadata — so each chunk carries its source context
3. **No overlap needed** — bullets are independent facts, not narrative text

**Example chunk**:
```
[Billing Policy] Late payment fee of IDR 50,000 applies after 14 days overdue
```

**Why NOT fixed-size chunking**:
- Our documents are structured as bullet lists, not prose
- Fixed-size chunks would split mid-sentence or merge unrelated bullets
- Bullet-level chunks give precise retrieval — a billing question retrieves
  only billing facts, not unrelated troubleshooting steps

**Why NOT sentence-level**:
- Our bullets ARE sentences — bullet-level = sentence-level here
- But we add the document title prefix for disambiguation

**Chunk metadata**:
```python
@dataclass
class Chunk:
    content: str          # The bullet point text with doc title prefix
    source: str           # Source document filename
    chunk_id: str         # Unique identifier
```

---

### Task B2: Embedding Generation (`src/rag/embeddings.py`)

**Model**: `gemini-embedding-001` (Gemini)

**Why this model**:
- Native integration with Gemini ecosystem (same API key, single SDK)
- 768-dimensional embeddings — good balance of quality vs. storage
- Strong multilingual support (important: Indonesian telco, IDR currency)
- Free tier: 1,500 requests/min — more than sufficient for this use case
- Task type support: `RETRIEVAL_DOCUMENT` for indexing, `RETRIEVAL_QUERY` for search

**Implementation**:
```python
async def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Generate embeddings using Gemini gemini-embedding-001."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config={"task_type": task_type},
    )
    return [e.values for e in result.embeddings]

async def embed_query(query: str) -> list[float]:
    """Embed a single query for retrieval."""
    return (await embed_texts([query], task_type="RETRIEVAL_QUERY"))[0]
```

---

### Task B3: FAISS Vector Store (`src/rag/vector_store.py`)

**Implementation**:
- Use `faiss.IndexFlatIP` (inner product / cosine similarity on normalized vectors)
- Normalize embeddings before indexing (L2 norm → cosine similarity)
- Persist index to disk (`data/faiss_index`)
- Maintain a parallel metadata store (list of Chunk objects, pickled)

**Why FAISS**:
- Zero infrastructure — runs in-process, no external service
- Fast for small datasets (our ~15 chunks)
- Easy to persist and reload
- Well-suited for assignment scope

**Why IndexFlatIP (not IVF/HNSW)**:
- Dataset is tiny (<100 vectors) — exact search is fine
- No approximation error
- Simpler to understand and debug

---

### Task B4: Retriever (`src/rag/retriever.py`)

```python
async def retrieve(query: str, top_k: int = 3, threshold: float = 0.3) -> list[RetrievalResult]:
    """
    1. Embed the query using RETRIEVAL_QUERY task type
    2. Search FAISS index for top_k nearest neighbors
    3. Filter results below similarity threshold
    4. Return chunks with scores
    """
```

**Similarity threshold** (0.3):
- Below this, chunks are considered irrelevant
- If no chunks pass the threshold → escalate to human
- Tuned empirically: billing questions should score >0.6, off-topic <0.2

---

### Task B5: Agent Service (`src/agent/service.py`)

**Orchestration flow**:

```
User message
    ↓
Retrieve relevant chunks (FAISS)
    ↓
No chunks pass threshold? → escalate: true, apologize
    ↓
Build prompt: system_prompt + context + conversation_history + user_message
    ↓
Call Gemini (gemini-3-flash-preview)
    ↓
Parse response for escalation signals
    ↓
Return ChatResponse(reply=..., escalate=..., sources=...)
```

**Escalation detection**:
- Explicit: no relevant chunks retrieved → `escalate: true`
- LLM-driven: system prompt instructs the model to indicate when it can't answer
- Parse LLM response for escalation phrases ("connect you with", "human agent", etc.)

**Conversation history handling**:
- Append conversation history as alternating user/assistant messages
- Limit to last 10 messages to stay within context window
- System prompt + context always takes priority

**Gemini call**:
```python
response = client.models.generate_content(
    model=settings.gemini_model,
    contents=messages,
    config=GenerateContentConfig(
        temperature=0.1,         # Low temperature for factual answers
        max_output_tokens=1024,
    ),
)
```

**Why temperature=0.1**:
- Customer service needs consistent, factual answers
- Higher temperature → more creative → more hallucination risk
- Not 0.0 because some flexibility helps with natural phrasing

**SDK usage** (`google-genai` — the only LLM library):
```python
from google import genai

client = genai.Client()  # reads GEMINI_API_KEY from env
```
No LangChain, no LlamaIndex, no `google-generativeai` — direct `google-genai` SDK only.

---

## Written Explanation (for README)

The README will include a section covering:

### 1. System Prompt Rationale
- Role grounding (Telco CS assistant persona)
- Strict context-only answering to prevent hallucination
- Explicit escalation rules
- Currency and formatting guidelines

### 2. Chunking Strategy
- Per-bullet-point chunking with document title prefix
- Why: structured KB with independent facts, not prose
- No overlap needed for this document structure
- Each chunk is self-contained and attributable

### 3. Embedding Model Choice
- Gemini `gemini-embedding-001`: native ecosystem integration, multilingual,
  768 dims, free tier, task-type-aware embeddings

### 4. One Limitation & Production Improvement
- **Limitation**: Static FAISS index — requires restart/re-ingestion when KB updates
- **Production fix**: Use a managed vector store (Qdrant/Pinecone) with incremental
  upsert, webhook-triggered re-indexing on document changes, and versioned embeddings
  for rollback capability

---

## Acceptance Criteria

- [x] `POST /chat` returns valid `ChatResponse` JSON
- [x] Agent answers billing questions using KB context
- [x] Agent answers plan questions using KB context
- [x] Agent answers troubleshooting questions using KB context
- [x] Agent sets `escalate: true` for off-topic questions
- [x] Agent sets `escalate: true` when no relevant chunks found
- [x] Agent does not hallucinate pricing or policies
- [x] Conversation history is respected across turns
- [x] `sources` field shows which documents were used
- [x] FAISS index persists to disk and reloads on startup
- [x] 20 unit tests passing (ingestion, vector store, escalation detection)
