# Phase 3: Deployment & Streamlit Demo

**Created**: 2026-04-08
**Priority**: ⭐⭐⭐⭐ HIGH (P1 — extra mile, strong impression on reviewers)
**Status**: ✅ COMPLETED (2026-04-08)
**Depends On**: Phase 0 (Setup), Phase 1 (Q1 Agent)
**Blocks**: Nothing

---

## Overview

Deploy the FastAPI backend and a Streamlit chat UI to Google Cloud Run via
GitHub Actions. Reviewers can test the live agent without cloning the repo.

**Architecture**:
```
Reviewer browser
    ↓
Streamlit (Cloud Run)  ──→  FastAPI API (Cloud Run)  ──→  Gemini API
                                    ↓
                               FAISS (in-memory, loaded on startup)
```

---

## Components

### 1. Streamlit Chat Frontend (`streamlit_app/`)

**Location**: `streamlit_app/app.py`

**Features**:
- `st.chat_message` interface — familiar chat UX
- Shows escalation badge when `escalate: true`
- Displays source documents used (from `sources` field)
- Conversation history maintained in `st.session_state`
- Calls FastAPI backend via `httpx`

**Layout**:
```
streamlit_app/
├── app.py              # Main Streamlit app
├── Dockerfile          # Separate Dockerfile for Streamlit
└── requirements.txt    # Streamlit-specific deps (streamlit, httpx)
```

**Key UI elements**:
- Title: "MyTelco Customer Service Agent"
- Sidebar: brief description, link to GitHub repo
- Chat area: user/assistant messages
- Escalation indicator: warning banner when agent escalates
- Source pills: show which KB docs were referenced

---

### 2. FastAPI Backend (existing from Q1)

No changes needed — the `/chat` endpoint already returns the right schema.
Add a `/health` endpoint for Cloud Run health checks.

FAISS index is baked into the Docker image (ingested at build time or on startup).

---

### 3. Dockerfiles

**Backend** (`Dockerfile`):
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
# Ingest knowledge base at build time (optional, or do on startup)
USER appuser
EXPOSE 8080
HEALTHCHECK CMD python -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Streamlit** (`streamlit_app/Dockerfile`):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY streamlit_app/ .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

### 4. GitHub Actions CI/CD

**Workflow**: `.github/workflows/deploy.yml`

**Triggers**: push to `main` branch

**Steps**:
1. Checkout code
2. Authenticate to GCP (Workload Identity Federation or service account key)
3. Build & push backend Docker image to Artifact Registry
4. Deploy backend to Cloud Run
5. Build & push Streamlit Docker image to Artifact Registry
6. Deploy Streamlit to Cloud Run (with `API_URL` env var pointing to backend)

**Environment variables (Cloud Run secrets)**:
- Backend: `GEMINI_API_KEY`
- Streamlit: `API_URL` (backend Cloud Run URL)

---

### 5. Cloud Run Configuration

| Service | CPU | Memory | Min Instances | Max Instances | Port |
|---------|-----|--------|---------------|---------------|------|
| `telco-agent-api` | 1 vCPU | 512 MiB | 0 (scale to zero) | 3 | 8080 |
| `telco-agent-ui` | 1 vCPU | 256 MiB | 0 (scale to zero) | 2 | 8501 |

**Region**: `asia-southeast1` (Jakarta — closest to Kata.ai)

---

## Tasks

### Task D1: Create Streamlit Chat App
- `st.chat_message` based UI
- Session state for conversation history
- httpx calls to FastAPI backend
- Escalation badge + source display

### Task D2: Create Dockerfiles
- Backend: multi-stage, non-root, health check
- Streamlit: simple single-stage

### Task D3: GitHub Actions Workflow
- CI: lint + test on PR
- CD: build + deploy to Cloud Run on push to main

### Task D4: Cloud Run Setup
- Create services via `gcloud` or Terraform
- Set secrets (GEMINI_API_KEY)
- Configure IAM (allow unauthenticated for demo)

---

## What to Include in README

- Live demo link: `https://telco-agent-ui-xxxxx-as.a.run.app`
- Note: "Deployed on Cloud Run (asia-southeast1) via GitHub Actions"
- Screenshot of the Streamlit UI

---

## Acceptance Criteria

- [x] Streamlit UI shows chat interface
- [x] Messages round-trip through FastAPI backend
- [x] Escalation shown visually in UI
- [x] Source documents displayed per response
- [x] GitHub Actions CI workflow (ci.yml)
- [x] GitHub Actions CD workflow (deploy.yml)
- [x] Backend Dockerfile (multi-stage, non-root)
- [x] Streamlit Dockerfile
- [ ] Cloud Run services deployed (pending: GCP SA key + Artifact Registry setup)
- [ ] Demo URL accessible to reviewers (pending deployment)
