**Technical Assignment**

AI Engineer – Associate / Mid Level

Engineering & Delivery Division

**Overview**

This assignment has two questions. Together they cover the full AI engineer stack — from building a working AI agent to designing and evaluating a production system.

We are not looking for a perfect system. We want to see how you think, how you make decisions under constraints, and how clearly you can explain your reasoning.

*Estimated time: 1–2 days. Depth of thinking matters more than completeness. A well-reasoned incomplete submission is better than a rushed one.*

**Scenario**

You are an AI Engineer building a Customer Service AI Agent for a telecommunications company. The agent handles inbound customer questions via chat — answering questions about service plans, billing, and basic troubleshooting — and escalates to a human agent when it cannot answer confidently.

The Telco has provided a knowledge base of product and support documents. You will use the sample documents below as your knowledge base for this assignment.

**Sample Knowledge Base**

*Use the content below as source documents. Copy into 3 separate .txt or .md files.*

**Document 1 — Billing Policy**

* Bills are generated on the 1st of every month

* Late payment fee of IDR 50,000 applies after 14 days overdue

* Customers can request a billing dispute within 30 days of the invoice date

* Auto-pay enrollment is available via the MyTelco app

**Document 2 — Service Plans**

* Basic Plan: IDR 99,000/month — 10GB data, unlimited calls

* Pro Plan: IDR 199,000/month — 50GB data, unlimited calls, 5GB hotspot

* Unlimited Plan: IDR 299,000/month — Unlimited data, calls, and 20GB hotspot

* All plans include free access to streaming partners on weekends

**Document 3 — Troubleshooting Guide**

* For slow internet: restart the device, check signal strength, toggle airplane mode

* For call quality issues: check for network congestion via the MyTelco app

* For billing errors: submit a ticket via the app or call 123 (free from any network)

* SIM card replacement available at any authorized store with valid ID

**Scoring**

| \# | Question | Areas Covered | Score | Weight |
| :---- | :---- | :---- | :---- | :---- |
| **Q1** | Build a Customer Service AI Agent | LLM integration, Prompt Engineering, RAG Pipeline | 50 pts | 50% |
| **Q2** | Design & Evaluate the Production System | System Design, AI Evaluation, Observability | 50 pts | 50% |
| **Total** |  |  | **100 pts** | **100%** |

  **Question 1  —  Build a Customer Service AI Agent**  

*Coding \+ Short Written Explanation*  **\[LLM Integration\]**  **\[Prompt Engineering\]**  **\[RAG Pipeline\]**

**What to Build**

Build a working AI agent that answers customer questions using the knowledge base above. The agent should be exposed as a simple API endpoint.

**1A — Conversational Endpoint**

Create a /chat endpoint using FastAPI (Python). It should:

* Accept a user message and conversation history as input

* Use an LLM of your choice — OpenAI GPT-4o, Anthropic Claude, or Google Gemini

* Apply a system prompt that defines the agent as a Telco customer service assistant

* Return a JSON response with the reply text and an escalate flag (true/false)

* Set escalate: true when the agent cannot answer confidently — do not guess or hallucinate

**1B — RAG Pipeline**

Extend the endpoint above to answer using the knowledge base:

* Ingest the 3 sample documents into a vector store (Qdrant, Chroma, FAISS, pgvector, or Pinecone)

* On each user message, retrieve relevant chunks and pass them as context to the LLM

* If no relevant chunks are retrieved, the agent should acknowledge it cannot help and set escalate: true

**What to Explain**

Include a short written section in your README or design doc covering:

* Your system prompt — why you structured it the way you did

* Your chunking strategy — chunk size, overlap, and the reasoning behind your choices

* Your embedding model choice and why

* One limitation of your current RAG approach and how you would improve it in production

**Scoring Breakdown**

| Criteria | What We Look For | Points |
| :---- | :---- | :---- |
| System prompt quality & role enforcement | Clear, specific, controls agent behavior | 10 pts |
| RAG pipeline — chunking & embedding strategy | Appropriate strategy with clear reasoning | 15 pts |
| Retrieval integration & context passing to LLM | Retrieved context actually used in answer | 15 pts |
| Fallback & escalation handling | Sensible behavior when no answer found | 10 pts |
| **Total** |  | **50 pts** |

*You may use LangChain, LlamaIndex, or call the LLM/vector store APIs directly. Any approach is valid. Include a .env.example — never commit real API keys.*

  **Question 2  —  Design & Evaluate the Production System**  

*Architecture Diagram \+ Written Document*  **\[System Design\]**  **\[AI Evaluation\]**  **\[Observability\]**

**Part A — System Design**

Design the full production architecture for this Telco Customer Service AI Agent. You do not need to build this — design and explain it clearly.

The production system must support:

* Multi-channel input — chat (web/mobile) and voice (inbound calls via SIP/telephony)

* A RAG pipeline backed by a knowledge base that can be updated without redeployment

* Human escalation — seamless handoff to a live agent when the AI cannot answer

* Conversation memory — agent remembers context within a session

* Basic monitoring of response quality, latency, and escalation rate

Deliverables for Part A:

* An architecture diagram showing all major components and how they connect

* A written explanation covering:

  * What each main component does

  * How voice input is handled differently from chat

  * How the knowledge base is updated when new documents are added

  * Where conversation memory lives and how it flows through the system

  * One scalability concern you foresee and how you would address it

**Part B — Evaluation & Observability**

Before this agent goes live and once it is running in production, you are responsible for measuring whether it is working well.

**Before Launch — Evaluation Strategy**

Describe how you would evaluate the agent before releasing to real users:

* What test dataset you would create and how

* What metrics you would use (e.g. answer accuracy, retrieval precision, hallucination rate)

* Whether you would use manual review, automated eval, or LLM-as-judge — and why

* What minimum passing threshold you would require before approving a release

**In Production — Monitoring & Observability**

Once live, describe what you would monitor:

* At least 3 specific metrics and why each one matters for this use case

* What tool(s) you would use — e.g. Langfuse, LangSmith, or custom logging

* How you would detect and respond to a sudden drop in answer quality

**Failure Mode Analysis**

Describe how you would handle these two specific failure scenarios:

* Scenario 1: The LLM starts producing hallucinated answers — making up billing policies that do not exist in the knowledge base

* Scenario 2: After a knowledge base update, the vector store starts retrieving irrelevant chunks for most queries

**Scoring Breakdown**

| Criteria | What We Look For | Points |
| :---- | :---- | :---- |
| Architecture diagram — completeness & clarity | All components present, clearly connected | 15 pts |
| Design reasoning — component & flow explanation | Technically sound, practical tradeoffs considered | 15 pts |
| Evaluation strategy — metrics & test approach | Meaningful metrics, realistic eval plan | 10 pts |
| Failure mode analysis & observability | Shows awareness of real production risks | 10 pts |
| **Total** |  | **50 pts** |

*For the diagram, any tool is fine — draw.io, Excalidraw, Lucidchart, or hand-drawn and photographed. We care about clarity of thinking, not the tool.*

**Deliverables Summary**

| \# | Deliverable | Format | For |
| :---- | :---- | :---- | :---- |
| 1 | Working code | GitHub repo or ZIP | Q1 |
| 2 | README with setup instructions | Markdown in repo | Q1 |
| 3 | Architecture diagram | PNG/PDF or draw.io / Excalidraw link | Q2 |
| 4 | Design & evaluation document | PDF or Markdown | Q2 |

**How to Submit**

1. Email your submission to \[fai@kata.ai\] with subject: AI Engineer Assignment – \[Your Full Name\]

2. Attach all deliverables or include a single GitHub / Google Drive link

3. Include a .env.example for any required API keys — never commit real credentials

4. Questions? Email us — we are happy to clarify anything

*We review every submission carefully and will provide feedback regardless of the outcome.*

***Good luck — we look forward to seeing your work.***

Engineering & Delivery Team