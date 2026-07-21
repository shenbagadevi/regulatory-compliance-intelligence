"""
Document Management UI.

Responsible for:
1. Uploading regulatory documents
2. Displaying uploaded documents
"""

from datetime import datetime
from pathlib import Path
from src.core.config import AppConfig
import requests
import streamlit as st

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

UPLOAD_URL = f"{API_BASE_URL}/documents/upload"

UPLOAD_DIRECTORY = AppConfig.UPLOAD_DIRECTORY


# ---------------------------------------------------------------------
# Upload Section
# ---------------------------------------------------------------------


def upload_document() -> None:
    """
    Display document upload section.
    """

    st.subheader("📂 Document Management")

    st.caption("Upload regulatory PDF documents to the compliance knowledge base.")

    uploaded_file = st.file_uploader(
        "Choose Regulatory PDF",
        type=["pdf"],
    )

    if st.button(
        "Upload Document",
        use_container_width=True,
    ):

        if uploaded_file is None:

            st.warning("Please choose a PDF document.")

            return

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file,
                "application/pdf",
            )
        }

        with st.spinner("Uploading document..."):

            try:

                response = requests.post(
                    UPLOAD_URL,
                    files=files,
                    timeout=60,
                )

            except requests.exceptions.RequestException:

                st.error("Unable to connect to FastAPI.")

                return

        if response.status_code == 201:

            result = response.json()

            st.success(result["message"])

            st.rerun()

        else:

            try:
                st.error(response.json()["detail"])
            except Exception:
                st.error("Upload failed.")


# ---------------------------------------------------------------------
# Uploaded Documents
# ---------------------------------------------------------------------


def show_uploaded_documents() -> None:
    """
    Display uploaded regulatory documents.
    """

    st.subheader("📄 Uploaded Documents")

    if not UPLOAD_DIRECTORY.exists():

        st.info("Upload directory not found.")

        return

    pdf_files = sorted(UPLOAD_DIRECTORY.glob("*.pdf"))

    if not pdf_files:

        st.info("No regulatory documents uploaded.")

        return

    st.caption(f"{len(pdf_files)} document(s) available")

    for pdf in pdf_files:

        stat = pdf.stat()

        size_mb = stat.st_size / (1024 * 1024)

        modified = datetime.fromtimestamp(stat.st_mtime)

        with st.container():

            col1, col2 = st.columns([5, 1])

            with col1:

                st.markdown(f"**📄 {pdf.name}**")

                st.caption(f"Last Modified : " f"{modified.strftime('%d-%b-%Y %H:%M')}")

                st.caption(f"Size : {size_mb:.2f} MB")

            with col2:

                st.success("Ready")

            st.divider()


# ---------------------------------------------------------------------
# Dashboard Metrics
# ---------------------------------------------------------------------


def document_metrics() -> None:
    """
    Display document statistics.
    """

    count = 0

    if UPLOAD_DIRECTORY.exists():

        count = len(list(UPLOAD_DIRECTORY.glob("*.pdf")))

    st.metric(
        "Documents",
        count,
    )
