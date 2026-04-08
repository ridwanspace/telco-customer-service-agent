# Phase 0: Project Setup & Scaffolding

**Created**: 2026-04-08
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL (P0 — foundation for all other work)
**Status**: ✅ COMPLETED (2026-04-08)
**Depends On**: Nothing
**Blocks**: Q1 (AI Agent), Q2 (Design Document)

---

## Overview

Set up the project structure, dependencies, tooling, and documentation scaffolding
for the Kata AI Technical Assignment. This follows the same conventions as our
`restaurant-erp-api` project: FastAPI, strict linting (Black + Ruff + Mypy),
pytest, and clean project layout.

**Tech Stack Decisions**:
- **LLM**: Google Gemini (via `google-genai` SDK)
- **Vector Store**: FAISS (local, no external service needed)
- **Embedding Model**: Gemini `text-embedding-004` (768 dims, free tier friendly)
- **Framework**: FastAPI + Uvicorn
- **Diagram Tool**: Excalidraw (for Q2 architecture diagram)

---

## Project Structure

```
kata-ai-interview/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py              # /chat endpoint
│   │   └── schemas.py             # Request/Response Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (env-based)
│   │   └── prompts.py             # System prompt definition
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py          # Embedding generation (Gemini)
│   │   ├── ingestion.py           # Document loading & chunking
│   │   ├── retriever.py           # FAISS similarity search
│   │   └── vector_store.py        # FAISS index management
│   └── agent/
│       ├── __init__.py
│       └── service.py             # LLM orchestration (retrieve → prompt → respond)
├── knowledge_base/
│   ├── billing_policy.md
│   ├── service_plans.md
│   └── troubleshooting_guide.md
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_ingestion.py
│   │   ├── test_retriever.py
│   │   └── test_agent.py
│   └── integration/
│       ├── __init__.py
│       └── test_chat_endpoint.py
├── plan/                          # This directory — design docs
│   ├── 00-project-setup.md
│   ├── 01-q1-ai-agent.md
│   └── 02-q2-system-design.md
├── docs/
│   └── architecture.excalidraw    # Q2 architecture diagram (Excalidraw)
├── data/                          # FAISS index persistence
│   └── .gitkeep
├── scripts/
│   └── ingest.py                  # Standalone ingestion script
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .pre-commit-config.yaml
├── .gitignore
├── Dockerfile
└── README.md
```

---

## Tasks

### Task S1: Initialize pyproject.toml

Adapt from `restaurant-erp-api` with project-specific values:

```toml
[project]
name = "telco-customer-service-agent"
version = "0.1.0"
description = "AI-powered Customer Service Agent for Telco — Kata.ai Technical Assignment"
requires-python = ">=3.12"

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.ruff]
target-version = "py312"
line-length = 100
# Same rule set as restaurant-erp-api

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

### Task S2: Create requirements.txt

**Core dependencies**:
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
google-genai>=1.0.0
faiss-cpu>=1.9.0
numpy>=1.26.0
python-dotenv>=1.0.0
httpx>=0.27.0
```

**Dev dependencies** (requirements-dev.txt):
```
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
black>=24.0.0
ruff>=0.8.0
mypy>=1.13.0
pre-commit>=4.0.0
```

---

### Task S3: Create .env.example

```env
# === Application ===
APP_NAME=telco-customer-service-agent
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# === Gemini AI ===
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-3-flash-preview
EMBEDDING_MODEL=text-embedding-004

# === RAG Settings ===
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=3
SIMILARITY_THRESHOLD=0.3

# === FAISS ===
FAISS_INDEX_PATH=data/faiss_index
```

---

### Task S4: Create Knowledge Base Files

Split the sample documents into 3 separate markdown files under `knowledge_base/`.

---

### Task S5: Create .gitignore

Standard Python + project-specific exclusions:
```
__pycache__/
*.py[cod]
.env
.venv/
venv/
data/faiss_index*
.mypy_cache/
.ruff_cache/
.pytest_cache/
dist/
build/
*.egg-info/
```

---

### Task S6: Create Dockerfile

Multi-stage build following restaurant-erp-api pattern:
- Builder stage: install deps in venv
- Runtime stage: non-root user, health check
- Expose port 8000
- CMD: uvicorn

---

### Task S7: Pre-commit Configuration

Same hooks as restaurant-erp-api:
1. Standard pre-commit hooks (trailing whitespace, YAML, merge conflicts)
2. Black (formatter)
3. Ruff (linter)
4. Mypy (type checker)

---

## Acceptance Criteria

- [x] `pip install -r requirements.txt` succeeds
- [x] `black --check src/` passes
- [x] `ruff check src/` passes
- [ ] `mypy src/` passes (once code is written)
- [ ] `pytest` runs without errors (once tests are written)
- [x] `.env.example` documents all required env vars
- [x] Project structure matches the layout above
