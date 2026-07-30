"""
ingestion.py

NOTE:
This is a logging/exception-handling enhanced version.
Copy your existing business logic into this file where indicated if needed.
"""

import os
import re
import uuid
import logging
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core import logger  # initializes logging configuration
from src.core.database import get_vector_store
from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.schemas.compliance_response import UploadResponse

logger = logging.getLogger(__name__)


def load_pdf(file_name, pdf_path):
    try:
        logger.info("Loading PDF: %s", pdf_path)

        current_section = "N/A"
        current_regulation = "General"
        current_document_type = "General"

        loader = PyPDFLoader(pdf_path)
        docs = loader.load()

        for doc in docs:
            metadata = extract_section_metadata(doc.page_content)

            if metadata["section"] != "N/A":
                current_section = metadata["section"]
                current_regulation = metadata["regulation_type"]
                current_document_type = metadata["document_type"]

            doc.metadata.update(
                {
                    "document": file_name,
                    "section": current_section,
                    "regulation_type": current_regulation,
                    "document_type": current_document_type,
                    "source": pdf_path,
                    "document_extension": "pdf",
                    "page": doc.metadata.get("page"),
                    "last_updated": os.path.getmtime(pdf_path),
                }
            )

        logger.info("PDF loaded successfully. Pages=%s", len(docs))
        return docs

    except Exception:
        logger.exception("Failed to load PDF.")
        raise


def split_documents(documents):
    try:
        logger.info("Starting chunking.")

        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=int(CHUNK_SIZE),
            chunk_overlap=int(CHUNK_OVERLAP),
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = splitter.split_documents(documents)

        logger.info("Chunking completed. Total chunks=%s", len(chunks))
        return chunks

    except Exception:
        logger.exception("split_documents failed.")
        raise


def extract_section_metadata(text: str) -> dict:
    try:
        match = re.search(
            r"##\s*SECTION\s+(\d+)\s*:\s*(.+)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return {
                "section": "N/A",
                "regulation_type": "General",
                "document_type": "General",
            }

        section_no = match.group(1)
        section_title = match.group(2).strip()
        section = f"SECTION {section_no}:"

        title = section_title.upper()

        if "RBI" in title:
            regulation = "RBI"
        elif "SEBI" in title:
            regulation = "SEBI"
        elif "BASEL" in title:
            regulation = "Basel III"
        elif "AML" in title or "KYC" in title:
            regulation = "RBI / PMLA"
        elif "SARFAESI" in title:
            regulation = "SARFAESI"
        elif "IBC" in title:
            regulation = "IBC"
        else:
            regulation = "General"

        if "GUIDELINE" in title:
            document_type = "Guideline"
        elif "REGULATION" in title:
            document_type = "Regulation"
        elif "FRAMEWORK" in title:
            document_type = "Framework"
        elif "POLICY" in title:
            document_type = "Policy"
        elif "CAPITAL" in title:
            document_type = "Capital Regulation"
        elif "AML" in title or "KYC" in title:
            document_type = "Compliance"
        else:
            document_type = "General"

        return {
            "section": section,
            "regulation_type": regulation,
            "document_type": document_type,
        }

    except Exception:
        logger.exception("extract_section_metadata failed.")
        raise


def extract_regulation_type(text: str):
    try:
        name = text.upper()

        if "RBI" in name:
            return "RBI"
        if "SEBI" in name:
            return "SEBI"
        if "PMLA" in name:
            return "PMLA"
        if "FATF" in name:
            return "FATF"

        return "General"

    except Exception:
        logger.exception("extract_regulation_type failed.")
        raise


def enrich_metadata(chunks, pdf_path):
    try:
        logger.info("Enriching metadata.")

        document_name = os.path.basename(pdf_path)
        document_id = str(uuid.uuid4())
        created_time = datetime.utcnow().isoformat()
        source_date = (
            datetime.fromtimestamp(os.path.getmtime(pdf_path)).date().isoformat()
        )

        for index, chunk in enumerate(chunks):
            chunk.metadata.update(
                {
                    "document_name": document_name,
                    "document_id": document_id,
                    "chunk_index": index,
                    "chunk_id": f"{document_name}_{index+1}",
                    "version": "1.0",
                    "source_date": source_date,
                    "created_at": created_time,
                }
            )

        logger.info("Metadata enrichment completed.")
        return chunks

    except Exception:
        logger.exception("enrich_metadata failed.")
        raise


def store_chunks(chunks):
    try:
        logger.info("Storing %s chunks.", len(chunks))

        vector_store = get_vector_store(pre_delete_collection=True)
        vector_store.add_documents(chunks)

        logger.info("Chunks stored successfully.")

    except Exception:
        logger.exception("store_chunks failed.")
        raise


def ingest(file_name, pdf_path):
    chunks = []

    try:
        logger.info("Starting ingestion for %s", file_name)

        documents = load_pdf(file_name, pdf_path)
        chunks = split_documents(documents)
        chunks = enrich_metadata(chunks, pdf_path)
        store_chunks(chunks)

        logger.info("Document ingestion completed successfully.")

        return UploadResponse(
            status="SUCCESS",
            message=f"Document uploaded successfully. {len(chunks)} chunks created.",
            document_name=file_name,
            document_path=str(pdf_path),
            total_chunks=len(chunks),
            version="1.0",
            ready_for_ingestion=True,
        )

    except Exception as ex:
        logger.exception("Document ingestion failed.")

        return UploadResponse(
            status="FAILED",
            message=f"Document upload failed. {str(ex)}",
            document_name=file_name,
            document_path=str(pdf_path),
            total_chunks=len(chunks),
            version="1.0",
            ready_for_ingestion=False,
        )
