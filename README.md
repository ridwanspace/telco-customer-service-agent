# MyTelco Customer Service AI Agent

AI-powered customer service agent for a telecommunications company, built as a technical assignment for Kata.ai.

The agent answers customer questions about **billing**, **service plans**, and **troubleshooting** using a RAG (Retrieval-Augmented Generation) pipeline. When it cannot answer confidently, it escalates to a human agent.

## Live Demo

| Service | URL |
|---------|-----|
| **Chat UI (Streamlit)** | [https://telco-agent-ui-840606066459.asia-southeast1.run.app](https://telco-agent-ui-840606066459.asia-southeast1.run.app) |
| **API (FastAPI)** | [https://telco-agent-api-840606066459.asia-southeast1.run.app](https://telco-agent-api-840606066459.asia-southeast1.run.app) |
| **API Docs (Swagger)** | [https://telco-agent-api-840606066459.asia-southeast1.run.app/docs](https://telco-agent-api-840606066459.asia-southeast1.run.app/docs) |

> Deployed on Google Cloud Run (`asia-southeast1` / Jakarta) via GitHub Actions. Services scale to zero when idle — first request may take a few seconds for cold start.

### Try It Out

1. Open the **[Chat UI](https://telco-agent-ui-840606066459.asia-southeast1.run.app)**
2. Ask questions like:
   - "What plans do you offer?"
   - "How much is the late payment fee?"
   - "My internet is slow, what should I do?"
   - "Can I get a refund for Netflix?" (should escalate)
3. The agent shows:
   - **Source documents** used to generate the answer
   - **Escalation warning** when it can't answer confidently

## Deliverables

| # | Deliverable | Format | For | Location |
|---|-------------|--------|-----|----------|
| 1 | Working code | GitHub repo | Q1 | [`src/`](src/) — FastAPI app, RAG pipeline, agent service |
| 2 | README with setup instructions | Markdown | Q1 | This file — see [Quick Start](#quick-start) and [Design Decisions](#design-decisions-q1) |
| 3 | Architecture diagram | Mermaid (renders on GitHub) | Q2 | [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) — 10 diagrams covering architecture, flows, and failure modes |
| 4 | Design & evaluation document | Markdown | Q2 | [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) — system design, evaluation strategy, observability, failure analysis |

**Bonus deliverables:**

| Deliverable | Location |
|-------------|----------|
| Live demo (Streamlit Chat UI) | [telco-agent-ui](https://telco-agent-ui-840606066459.asia-southeast1.run.app) |
| Live API (FastAPI + Swagger) | [telco-agent-api](https://telco-agent-api-840606066459.asia-southeast1.run.app/docs) |
| CI/CD pipeline (GitHub Actions) | [`.github/workflows/`](.github/workflows/) |
| Unit tests (20 tests) | [`tests/`](tests/) |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI |
| **LLM** | Google Gemini (`gemini-3-flash-preview`) |
| **Embeddings** | Gemini Embedding (`gemini-embedding-001`) |
| **Vector Store** | FAISS (local, in-process) |
| **Frontend** | Streamlit |
| **Deployment** | Google Cloud Run + GitHub Actions |
| **Code Quality** | Black, Ruff, Mypy, Pytest |

## Quick Start

### Prerequisites

- Python 3.11+
- A [Google AI Studio](https://aistudio.google.com/) API key for Gemini

### Setup

```bash
# Clone the repository
git clone https://github.com/ridwanspace/telco-customer-service-agent.git
cd telco-customer-service-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Run the API

```bash
uvicorn src.main:app --reload --port 8000
```

On first startup, the app ingests the knowledge base and builds the FAISS index. Subsequent starts load from disk.

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What plans do you offer?"}'
```

### Run the Streamlit UI

```bash
pip install -r streamlit_app/requirements.txt
API_URL=http://localhost:8000 streamlit run streamlit_app/app.py
```

### Run Tests

```bash
pip install -r requirements-dev.txt
pytest tests/unit/ -v
```

## API Reference

### `POST /chat`

Chat with the AI agent.

**Request:**
```json
{
    "message": "What is the late payment fee?",
    "conversation_history": [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello! How can I help you today?"}
    ]
}
```

**Response:**
```json
{
    "reply": "The late payment fee is IDR 50,000, which applies after 14 days overdue.",
    "escalate": false,
    "sources": ["billing_policy"]
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "faiss_loaded": true,
    "document_count": 12
}
```

## Project Structure

```
├── src/
│   ├── main.py              # FastAPI app with lifespan (FAISS init)
│   ├── api/
│   │   ├── router.py        # /chat and /health endpoints
│   │   └── schemas.py       # Pydantic request/response models
│   ├── core/
│   │   ├── config.py        # Settings from environment
│   │   └── prompts.py       # System prompt definition
│   ├── rag/
│   │   ├── ingestion.py     # Document loading & chunking
│   │   ├── embeddings.py    # Gemini embedding generation
│   │   ├── vector_store.py  # FAISS index management
│   │   └── retriever.py     # Similarity search & context formatting
│   └── agent/
│       └── service.py       # LLM orchestration & escalation detection
├── knowledge_base/           # Source documents (3 files)
├── streamlit_app/            # Chat UI frontend
├── tests/                    # Unit tests (20 tests)
├── docs/
│   └── SYSTEM_DESIGN.md     # Q2: Architecture & evaluation document (with Mermaid diagrams)
├── plan/                     # Development plan documents
└── .github/workflows/        # CI/CD pipelines
```

## Design Decisions (Q1)

### System Prompt

The system prompt is structured with explicit rules to control agent behavior:

1. **Role grounding** — defines the agent as a MyTelco customer service assistant, establishing persona and scope
2. **Context-only answering** — the most critical rule. The agent is instructed to ONLY use retrieved context, preventing hallucination of pricing, policies, or procedures
3. **Explicit escalation format** — uses an `ESCALATE:` prefix for clear, parseable escalation signals
4. **Currency enforcement** — always include IDR to avoid ambiguity with other currencies
5. **Frustration detection** — real customer service agents escalate emotional situations; the AI should too

This structure prioritizes **safety over helpfulness** — it's better to escalate than to give wrong billing information.

### Chunking Strategy

**Approach: Per-bullet-point chunking with document title prefix.**

Each bullet point from the knowledge base becomes a single chunk, prefixed with its source document title:
```
[Billing Policy] Late payment fee of IDR 50,000 applies after 14 days overdue
```

**Why this approach (not fixed-size chunking):**
- The knowledge base is structured as bullet lists, not narrative prose
- Each bullet is a self-contained, independent fact
- Fixed-size chunking would either split mid-bullet or merge unrelated facts
- Bullet-level granularity gives precise retrieval — a billing question retrieves only billing facts

**No overlap needed** because bullets are independent units. Overlap is valuable for narrative text where context spans sentences; our KB doesn't have that property.

### Embedding Model

**Model: `gemini-embedding-001`** (3072 dimensions)

- **Native ecosystem integration** — same Google AI SDK (`google-genai`) and API key as the LLM. Single dependency, no additional credentials.
- **Task-type-aware** — supports `RETRIEVAL_DOCUMENT` for indexing and `RETRIEVAL_QUERY` for search, optimizing embeddings for their purpose
- **Strong multilingual support** — important for an Indonesian telco (IDR currency, potential Bahasa Indonesia queries)
- **Free tier** — generous rate limits for development and demo usage

### One Limitation & Production Improvement

**Limitation:** Static FAISS index — the vector store is built at startup and lives in-memory. Adding or updating knowledge base documents requires restarting the service and re-embedding everything.

**Production improvement:** Replace FAISS with a managed vector store (Qdrant, Pinecone, or pgvector) that supports:
- **Incremental upsert** — add/update individual documents without rebuilding the entire index
- **Webhook-triggered re-indexing** — GCS file change → Pub/Sub → Cloud Function → re-embed & upsert
- **Versioned collections** — alias-based switching for zero-downtime updates with instant rollback
- **Eval gate** — automated quality check on new embeddings before going live

## Q2: System Design & Evaluation

See [`docs/SYSTEM_DESIGN.md`](docs/SYSTEM_DESIGN.md) for the full production architecture design, evaluation strategy, observability plan, and failure mode analysis. All diagrams are rendered as Mermaid and display natively on GitHub.

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
black src/ tests/ scripts/

# Lint
ruff check src/ tests/ scripts/

# Run tests
pytest tests/unit/ -v

# Run tests with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing
```

## Deployment

The application deploys to Google Cloud Run via GitHub Actions:

- **CI** (`.github/workflows/ci.yml`) — runs on every PR: format check, lint, unit tests
- **CD** (`.github/workflows/deploy.yml`) — deploys on push to `main`: builds Docker images, pushes to Artifact Registry, deploys backend + frontend to Cloud Run

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GCP_SA_KEY` | GCP service account key JSON (with Cloud Run, Artifact Registry permissions) |
| `GEMINI_API_KEY` | Google AI Studio API key |
