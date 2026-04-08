"""Streamlit Chat UI for MyTelco Customer Service Agent."""

import os

import httpx
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MyTelco Customer Service",
    page_icon="📱",
    layout="centered",
)

st.title("📱 MyTelco Customer Service Agent")
st.caption("AI-powered assistant for billing, plans, and troubleshooting")

with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "This AI agent helps MyTelco customers with:\n"
        "- **Billing** — invoices, late fees, disputes\n"
        "- **Service Plans** — Basic, Pro, Unlimited\n"
        "- **Troubleshooting** — internet, calls, SIM\n\n"
        "When the agent can't help, it escalates to a human agent."
    )
    st.divider()
    st.markdown(
        "Built with [FastAPI](https://fastapi.tiangolo.com/) + "
        "[Google Gemini](https://ai.google.dev/) + "
        "[FAISS](https://github.com/facebookresearch/faiss)"
    )
    st.markdown(
        "[📂 GitHub Repository](https://github.com/ridwanspace/telco-customer-service-agent)"
    )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("escalate"):
            st.warning("⚠️ This query has been escalated to a human agent.")
        if msg.get("sources"):
            source_labels = [s.replace("_", " ").title() for s in msg["sources"]]
            st.caption(f"📄 Sources: {', '.join(source_labels)}")

# Chat input
if prompt := st.chat_input("Ask about billing, plans, or troubleshooting..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build conversation history for API
    conversation_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    f"{API_URL}/chat",
                    json={
                        "message": prompt,
                        "conversation_history": conversation_history,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                reply = data["reply"]
                escalate = data.get("escalate", False)
                sources = data.get("sources", [])

                st.markdown(reply)
                if escalate:
                    st.warning("⚠️ This query has been escalated to a human agent.")
                if sources:
                    source_labels = [s.replace("_", " ").title() for s in sources]
                    st.caption(f"📄 Sources: {', '.join(source_labels)}")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": reply,
                        "escalate": escalate,
                        "sources": sources,
                    }
                )

            except httpx.HTTPStatusError as e:
                st.error(f"API error: {e.response.status_code}")
            except httpx.ConnectError:
                st.error(
                    "Cannot connect to the API. "
                    "Make sure the FastAPI backend is running."
                )
            except httpx.ReadTimeout:
                st.error("Request timed out. Please try again.")
