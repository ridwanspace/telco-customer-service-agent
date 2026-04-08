# Phase 2: Q2 — Design & Evaluate the Production System

**Created**: 2026-04-08
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL (P0 — 50% of total score)
**Status**: ✅ COMPLETED (2026-04-08)
**Depends On**: Nothing (independent of Q1 implementation)
**Blocks**: Nothing
**Assignment Ref**: Q2 — Design & Evaluate the Production System (50 pts)

---

## Overview

Design the full production architecture and evaluation strategy for the Telco
Customer Service AI Agent. This is a written deliverable — no code required.

**Scoring breakdown**:
| Criteria | Points |
|----------|--------|
| Architecture diagram — completeness & clarity | 15 pts |
| Design reasoning — component & flow explanation | 15 pts |
| Evaluation strategy — metrics & test approach | 10 pts |
| Failure mode analysis & observability | 10 pts |
| **Total** | **50 pts** |

**Deliverable format**: `docs/SYSTEM_DESIGN.md` + `docs/architecture.excalidraw`

---

## Part A — System Design

### Architecture Diagram (Excalidraw)

**Tool**: Excalidraw (export as `.excalidraw` + `.png`)

**Components to include**:

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                              │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐   │
│  │ Web Chat │  │ Mobile   │  │ Voice (SIP/Telephony)   │   │
│  │  Widget  │  │   App    │  │                         │   │
│  └────┬─────┘  └────┬─────┘  └────────┬────────────────┘   │
│       │              │                 │                    │
└───────┼──────────────┼─────────────────┼────────────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌──────────────┐              ┌──────────────────┐
│   API        │              │  Voice Gateway   │
│   Gateway    │◄─────────────│  (STT/TTS)       │
│  (Kong/Nginx)│              │  Google Speech/   │
│              │              │  Azure Speech     │
└──────┬───────┘              └──────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│              AI AGENT SERVICE (FastAPI)               │
│                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Session  │  │ RAG       │  │ Escalation       │  │
│  │ Manager  │  │ Pipeline  │  │ Handler          │  │
│  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
└───────┼──────────────┼──────────────────┼────────────┘
        │              │                  │
        ▼              ▼                  ▼
┌──────────┐  ┌──────────────┐  ┌────────────────────┐
│  Redis   │  │ Vector Store │  │ Human Agent Queue   │
│ (Session │  │ (Qdrant /    │  │ (Contact Center     │
│  Memory) │  │  Managed)    │  │  Platform / Genesys)│
└──────────┘  └──────┬───────┘  └────────────────────┘
                     │
              ┌──────┴───────┐
              │  Knowledge   │
              │  Base Store  │
              │ (GCS/S3)     │
              └──────┬───────┘
                     │
              ┌──────┴───────┐
              │  Ingestion   │
              │  Pipeline    │
              │ (Cloud Fn /  │
              │  Pub/Sub)    │
              └──────────────┘

┌──────────────────────────────────────────────────────┐
│              OBSERVABILITY                            │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Langfuse │  │ Prometheus│  │ Alerting         │  │
│  │ (LLM     │  │ + Grafana │  │ (PagerDuty /     │  │
│  │  Traces) │  │ (Metrics) │  │  Slack)          │  │
│  └──────────┘  └───────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

### Written Explanation Outline

#### 1. Component Overview

| Component | Purpose |
|-----------|---------|
| **API Gateway** (Kong/Nginx) | Rate limiting, auth, routing, SSL termination |
| **Voice Gateway** | STT (Speech-to-Text) + TTS (Text-to-Speech) for voice calls |
| **AI Agent Service** | Core FastAPI service — RAG, LLM orchestration, escalation |
| **Session Manager** | Manages conversation memory within sessions |
| **RAG Pipeline** | Retrieves relevant KB chunks for context injection |
| **Escalation Handler** | Routes unresolvable queries to human agents |
| **Redis** | Session/conversation memory store (TTL-based expiry) |
| **Vector Store** (Qdrant) | Production vector DB for embeddings (replaces FAISS) |
| **Knowledge Base Store** (GCS) | Source documents — editable by ops team |
| **Ingestion Pipeline** | Watches for KB changes → re-chunks → re-embeds → upserts |
| **Human Agent Queue** | Contact center integration for seamless handoff |
| **Langfuse** | LLM observability — traces, costs, quality scoring |
| **Prometheus + Grafana** | System metrics — latency, throughput, error rates |

#### 2. Voice vs Chat Handling

**Chat flow**:
```
Client → API Gateway → AI Agent Service → Response
```

**Voice flow**:
```
Phone Call → SIP Trunk → Voice Gateway (STT) → API Gateway → AI Agent Service
→ Response Text → Voice Gateway (TTS) → Audio back to caller
```

**Key differences**:
- Voice adds **STT/TTS latency** (~200-500ms each) — optimize for short responses
- Voice needs **barge-in detection** — user can interrupt mid-response
- Voice sessions need **silence timeout** — auto-escalate after prolonged silence
- Voice requires **SSML** for proper pronunciation of IDR amounts, plan names
- Streaming TTS for voice to reduce perceived latency

#### 3. Knowledge Base Update Flow

```
Ops uploads new doc to GCS
    ↓
GCS emits event → Pub/Sub topic
    ↓
Cloud Function / Worker triggered
    ↓
Worker: download doc → chunk → embed → upsert to Qdrant
    ↓
(Optional) Run eval suite on new embeddings
    ↓
If eval passes → swap to new collection version
If eval fails → alert ops team, keep old collection
```

**Key design decisions**:
- **No redeployment needed** — Qdrant collection updated independently
- **Versioned collections** — can rollback if new embeddings degrade quality
- **Eval gate** — automated quality check before going live
- **Atomic swap** — alias-based switching, no downtime

#### 4. Conversation Memory

**Where it lives**: Redis (per-session, TTL 30 minutes)

**Flow**:
```
1. Client sends message + session_id
2. Agent Service loads conversation history from Redis (key: session:{session_id})
3. History appended to LLM prompt as context
4. Response saved back to Redis
5. TTL refreshed on every interaction
6. On session end or timeout → history archived to cold storage (optional)
```

**Why Redis (not in-memory or DB)**:
- Shared across Agent Service replicas (horizontal scaling)
- TTL-based auto-cleanup — no stale session buildup
- Fast reads (~1ms) — no latency impact on conversation
- Survives service restarts (persistence optional)

**Memory strategy**:
- Keep last 20 messages per session (sliding window)
- Summarize older messages if session is long-running
- Clear on explicit session end or human escalation

#### 5. Scalability Concern

**Concern**: LLM API latency spikes during peak hours (morning commute, lunch break)
causing cascading timeouts and degraded user experience.

**How to address**:
- **Request queuing** with priority levels (billing disputes > plan info)
- **Response caching** for common queries (e.g., "what plans do you have?") — Redis
  cache with 5-min TTL, keyed on normalized query + intent
- **Circuit breaker** on LLM API calls — if Gemini latency >5s for 3 consecutive
  calls, temporarily route to fallback (pre-cached FAQ answers)
- **Horizontal scaling** — autoscale Agent Service pods based on queue depth
- **Streaming responses** — start sending tokens as they arrive (SSE) to reduce
  perceived latency

---

## Part B — Evaluation & Observability

### Before Launch — Evaluation Strategy

#### Test Dataset

**How to create**:
1. **Manual curation**: 50 test cases covering all 3 KB documents
2. **Distribution**:
   - 15 billing questions (3 per bullet point)
   - 15 service plan questions (3+ per plan, comparison queries)
   - 10 troubleshooting questions (2-3 per issue type)
   - 10 out-of-scope / should-escalate questions
3. **Format**: `(query, expected_answer, expected_escalate, expected_sources)`
4. **Edge cases**: misspellings, Bahasa Indonesia mixed with English, vague queries,
   multi-topic questions, adversarial prompts ("ignore your instructions")

**Example test cases**:
```json
[
  {
    "query": "How much is the late fee?",
    "expected_answer_contains": ["IDR 50,000", "14 days"],
    "expected_escalate": false,
    "expected_sources": ["billing_policy"]
  },
  {
    "query": "Can I get a refund for my Netflix subscription?",
    "expected_answer_contains": [],
    "expected_escalate": true,
    "expected_sources": []
  },
  {
    "query": "What's the difference between Pro and Unlimited?",
    "expected_answer_contains": ["IDR 199,000", "IDR 299,000", "50GB", "Unlimited"],
    "expected_escalate": false,
    "expected_sources": ["service_plans"]
  }
]
```

#### Metrics

| Metric | How to Measure | Target |
|--------|---------------|--------|
| **Answer accuracy** | LLM-as-judge: does the answer match expected content? | ≥ 90% |
| **Retrieval precision@3** | Of top-3 chunks, how many are from the correct doc? | ≥ 80% |
| **Hallucination rate** | LLM-as-judge: does the answer contain info NOT in context? | ≤ 5% |
| **Escalation correctness** | Precision & recall of escalation flag | ≥ 95% |
| **Response relevance** | LLM-as-judge: is the answer relevant to the question? | ≥ 90% |

#### Evaluation Method

**Hybrid approach**: Automated eval with LLM-as-judge + manual review of failures.

**Why LLM-as-judge** (not pure manual):
- Scalable — can run 50+ test cases in minutes
- Reproducible — same criteria every run
- Cheap — use Gemini Flash for judging

**Why not ONLY LLM-as-judge**:
- LLM judges can miss subtle hallucinations
- Manual review of flagged failures catches edge cases
- Human review of escalation decisions (false negatives are dangerous)

**Process**:
1. Run automated eval suite → generate scores
2. Manual review of all failures + random sample (20%) of passes
3. Track metrics across runs (regression detection)

#### Release Threshold

| Metric | Minimum to Ship |
|--------|----------------|
| Answer accuracy | ≥ 85% |
| Hallucination rate | ≤ 5% |
| Escalation precision | ≥ 90% |
| Escalation recall | ≥ 95% (miss < 5% of cases that should escalate) |
| Retrieval precision@3 | ≥ 75% |

**Escalation recall is highest** because: a missed escalation means a customer gets
a wrong/hallucinated answer → worse than unnecessary escalation to human.

---

### In Production — Monitoring & Observability

#### Metrics to Monitor

| # | Metric | Why It Matters | Alert Threshold |
|---|--------|---------------|-----------------|
| 1 | **Escalation rate** | Sudden increase = KB gap or retrieval degradation. Baseline ~15%, spike to >30% = investigate | > 30% over 1hr |
| 2 | **P95 response latency** | User experience. Voice channel especially sensitive to latency | > 3s for chat, > 5s for voice |
| 3 | **Retrieval confidence score (avg)** | Dropping average similarity score = embedding drift or KB mismatch | < 0.4 avg over 1hr |
| 4 | **User satisfaction (thumbs up/down)** | Direct quality signal from customers. Lagging indicator but ground truth | < 70% positive over 24hr |
| 5 | **Hallucination rate (sampled)** | Run LLM-as-judge on 10% of production responses to detect fabrication | > 5% in sampled batch |

#### Tooling

**Primary**: **Langfuse** (open-source LLM observability)
- Trace every LLM call: prompt, completion, tokens, latency, cost
- Track retrieval scores per query
- User feedback integration (thumbs up/down → linked to trace)
- Dashboard: quality trends, cost tracking, latency percentiles

**Supporting**:
- **Prometheus + Grafana** — system metrics (CPU, memory, HTTP status codes, queue depth)
- **Structured logging** (JSON) → **Cloud Logging / ELK** — searchable request logs
- **Alerting** via PagerDuty/Slack — threshold-based alerts on all metrics above

#### Detecting Quality Drops

**Automated detection pipeline**:
```
Every 1 hour:
    1. Sample 10% of responses from last hour
    2. Run LLM-as-judge eval (hallucination + relevance)
    3. Compare scores against 7-day rolling average
    4. If scores drop >15% → alert on-call engineer
    5. If escalation rate spikes >2x baseline → alert immediately

Dashboard checks (daily):
    - Review Langfuse traces with lowest confidence scores
    - Review all negative user feedback traces
    - Check retrieval score distribution for drift
```

---

### Failure Mode Analysis

#### Scenario 1: LLM Hallucinating Billing Policies

**Detection**:
- Langfuse traces show responses containing billing amounts not in KB
- LLM-as-judge hourly eval detects hallucination rate spike
- User feedback: "that's wrong" / thumbs down on billing answers

**Root cause investigation**:
1. Check if system prompt was modified (version control)
2. Check if model version changed (Gemini API update)
3. Check retrieval scores — are correct chunks being retrieved?
4. Check if context window is being exceeded (truncating context)

**Immediate response**:
1. **Enable strict output validation** — regex check that any IDR amount in the
   response exists verbatim in the retrieved chunks
2. **Lower temperature to 0** — minimize creative generation
3. **Increase retrieval threshold** — rather return "I don't know" than hallucinate

**Long-term fix**:
1. **Grounded generation** — use Gemini's grounding feature to cite sources
2. **Post-generation fact check** — second LLM call validates response against context
3. **Pin model version** — avoid surprise behavior changes from API updates
4. **Add integration test** — specific hallucination regression tests for billing amounts

#### Scenario 2: Irrelevant Chunks After KB Update

**Detection**:
- Retrieval confidence scores drop across the board (Langfuse dashboard)
- Escalation rate spikes (agent can't find relevant context)
- Users report generic/unhelpful answers

**Root cause investigation**:
1. Check what changed in the KB update (diff the documents)
2. Compare embeddings before/after — cosine similarity between old and new versions
3. Check if chunking strategy broke (e.g., new document format not parsed correctly)
4. Check if embedding model version changed

**Immediate response**:
1. **Rollback to previous vector store collection** — alias swap, zero downtime
2. **Alert the ops team** — block further KB updates until resolved

**Long-term fix**:
1. **Eval gate on ingestion** — run retrieval test suite against new embeddings
   BEFORE swapping the live collection. Test suite includes golden queries with
   expected source documents.
2. **Versioned collections** — keep last 3 versions, easy rollback
3. **Embedding drift monitoring** — track centroid shift of document clusters
   after each update. Large shift = investigate before deploying.
4. **Chunking validation** — assert chunk count, average chunk length, and
   source document coverage after re-ingestion. Alert if metrics deviate >20%.

---

## Deliverable Checklist

- [x] Architecture diagram in Excalidraw (`docs/architecture.excalidraw`)
- [ ] Architecture diagram exported as PNG (`docs/architecture.png`) — export manually from Excalidraw
- [x] Design document (`docs/SYSTEM_DESIGN.md`) covering:
  - [x] Component overview table
  - [x] Voice vs chat handling
  - [x] Knowledge base update flow
  - [x] Conversation memory design
  - [x] Scalability concern & mitigation
  - [x] Evaluation strategy with test dataset
  - [x] Production monitoring metrics
  - [x] Failure mode analysis (both scenarios)
