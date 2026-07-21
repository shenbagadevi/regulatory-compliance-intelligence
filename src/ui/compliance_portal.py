"""
Streamlit UI for Regulatory Compliance Intelligence System.

Enterprise portal integrating:
- Authentication
- Admin document management
- Compliance chatbot
- FastAPI backend
"""

import streamlit as st

from src.ui.auth import initialize_session, login, logout, sidebar_profile, is_admin

from src.ui.document_manager import (
    upload_document,
    show_uploaded_documents,
)

import requests

API_BASE_URL = "http://127.0.0.1:8000/api/v1"
QUERY_URL = f"{API_BASE_URL}/query"


st.set_page_config(
    page_title="Regulatory Compliance Intelligence System",
    page_icon="📘",
    layout="wide",
)


initialize_session()

login()


# Sidebar
with st.sidebar:

    sidebar_profile()

    st.divider()

    logout()

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if is_admin():

        st.divider()

        upload_document()

        st.divider()

        show_uploaded_documents()


# Header

header1, header2 = st.columns([8, 2])

with header1:
    st.title("Regulatory Compliance Intelligence System")
    st.caption("AI Powered Regulatory Knowledge Assistant")

with header2:
    st.success("🟢 System Online")


st.divider()


# Dashboard Metrics

documents = 0

try:
    from src.ui.document_manager import UPLOAD_DIRECTORY

    if UPLOAD_DIRECTORY.exists():
        documents = len(list(UPLOAD_DIRECTORY.glob("*.pdf")))

except Exception:
    pass


col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Documents", documents)

with col2:
    st.metric("Role", st.session_state.role)

with col3:
    st.metric(
        "Chat Messages",
        len(st.session_state.messages),
    )


st.divider()


# Chat History

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":

            st.markdown(message["content"])

        else:

            st.subheader("Answer")

            st.info(message["answer"])

            with st.expander(
                "Rule Summary",
                expanded=True,
            ):

                for rule in message["rule_summary"]:
                    st.write(f"✔ {rule}")

            confidence = message["confidence_score"]

            st.metric(
                "Confidence",
                f"{confidence * 100:.0f}%",
            )

            st.progress(confidence)

            with st.expander("Citations"):

                for citation in message["citations"]:

                    st.write(f"📄 {citation['document']}")

                    st.caption(f"Section: {citation['section']}")

                    st.caption(f"Page: {citation['page']}")

                    st.divider()

            st.caption(message["disclaimer"])


# Chat Input

question = st.chat_input("Ask a regulatory compliance question...")


if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Searching regulatory knowledge base..."):

            try:

                response = requests.post(
                    QUERY_URL,
                    json={"query": question},
                    timeout=60,
                )

            except requests.exceptions.RequestException:

                st.error("Unable to connect to FastAPI service.")

                st.stop()

        if response.status_code == 200:

            result = response.json()

            st.subheader("Answer")

            st.info(result["answer"])

            with st.expander(
                "Rule Summary",
                expanded=True,
            ):

                for rule in result["rule_summary"]:
                    st.write(f"✔ {rule}")

            confidence = result["confidence_score"]

            st.metric(
                "Confidence",
                f"{confidence * 100:.0f}%",
            )

            st.progress(confidence)

            with st.expander("Citations"):

                for citation in result["citations"]:

                    st.write(f"📄 {citation['document']}")

                    st.caption(f"Section: {citation['section']}")

                    st.caption(f"Page: {citation['page']}")

            st.caption(result["disclaimer"])

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "answer": result["answer"],
                    "rule_summary": result["rule_summary"],
                    "confidence_score": result["confidence_score"],
                    "citations": result["citations"],
                    "disclaimer": result["disclaimer"],
                }
            )

        else:

            st.error("Unable to process compliance query.")

            st.error(response.text)


st.divider()

st.caption(
    "Regulatory Compliance Intelligence System | "
    "FastAPI • LangChain • PostgreSQL • OpenAI"
)
