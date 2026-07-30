import os
import re
import uuid
import logging

from datetime import datetime, UTC

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.database import get_vector_store
from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.schemas.compliance_response import UploadResponse

logger = logging.getLogger(__name__)


def load_pdf(file_name, pdf_path):
    """
    Loads the PDF document.

    Args:
        file_name (str): Name of the uploaded document.
        pdf_path (str): Path of the PDF file.

    Returns:
        list: List of LangChain Document objects.
    """

    try:
        logger.info("Starting PDF loading. File: %s", file_name)

        current_section = "N/A"
        current_regulation = "General"
        current_document_type = "General"

        loader = PyPDFLoader(pdf_path)
        docs = loader.load()

        # logger.info("PDF loaded successfully. Total pages: %d", len(docs))

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

        # logger.info("Metadata enrichment completed for PDF pages.")

        return docs

    except Exception:
        logger.exception("Failed to load PDF: %s", pdf_path)
        raise


def split_documents(documents):
    """
    Splits the document into chunks using the
    project-specified chunking strategy.

    Returns:
        list: List of document chunks.
    """

    try:
        """
        logger.info(
            "Starting document chunking. Chunk Size=%s, Chunk Overlap=%s",
            CHUNK_SIZE,
            CHUNK_OVERLAP,
        )
        """

        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=int(CHUNK_SIZE),
            chunk_overlap=int(CHUNK_OVERLAP),
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = splitter.split_documents(documents)

        logger.info(
            "Chunking completed successfully. Total chunks created: %d",
            len(chunks),
        )

        return chunks

    except Exception:
        logger.exception("Failed while splitting documents.")
        raise


def extract_section_metadata(text: str) -> dict:
    """
    Extract section information from page text.

    Example:
        ## SECTION 4: KYC & AML

    Returns:
    {
        "section": "SECTION 4",
        "regulation_type": "RBI / PMLA",
        "document_type": "Guideline"
    }
    """

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

    # Regulation Type

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

    # Document Type

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


def extract_regulation_type(text: str):
    """
    Extract regulation type based on document content.
    """

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


def enrich_metadata(chunks, pdf_path):
    """
    Adds custom metadata to every chunk.

    Metadata:
        - document_name
        - document_id
        - chunk_index
        - chunk_id
        - version
        - source_date
        - created_at
    """

    try:
        # logger.info("Starting metadata enrichment.")

        document_name = os.path.basename(pdf_path)
        document_id = str(uuid.uuid4())

        created_time = datetime.now(UTC).isoformat()

        source_date = (
            datetime.fromtimestamp(
                os.path.getmtime(pdf_path),
                UTC,
            )
            .date()
            .isoformat()
        )

        version = "1.0"

        for index, chunk in enumerate(chunks):

            chunk.metadata.update(
                {
                    "document_name": document_name,
                    "document_id": document_id,
                    "chunk_index": index,
                    "chunk_id": f"{document_name}_{index + 1}",
                    "version": version,
                    "source_date": source_date,
                    "created_at": created_time,
                }
            )

        """
        logger.info(
            "Metadata enrichment completed successfully for %d chunks.",
            len(chunks),
        )
        """

        return chunks

    except Exception:
        logger.exception(
            "Failed while enriching metadata for document: %s",
            pdf_path,
        )
        raise


def store_chunks(chunks):
    """
    Store document chunks in PGVector.

    During ingestion:
        pre_delete_collection=True

    During retrieval:
        pre_delete_collection=False
    """

    try:
        # logger.info("Connecting to PGVector.")

        vector_store = get_vector_store(pre_delete_collection=True)

        vector_store.add_documents(chunks)

    except Exception:
        logger.exception("Failed while storing document chunks in PGVector.")
        raise


def ingest(file_name, pdf_path):
    """
    Complete ingestion pipeline.

    Steps:
        1. Load PDF
        2. Split document
        3. Enrich metadata
        4. Store chunks

    Returns:
        UploadResponse
    """

    chunks = []

    try:
        logger.info(
            "Document ingestion started. File: %s",
            file_name,
        )

        documents = load_pdf(
            file_name=file_name,
            pdf_path=pdf_path,
        )

        chunks = split_documents(documents)

        chunks = enrich_metadata(
            chunks,
            pdf_path,
        )

        store_chunks(chunks)

        logger.info(
            "Document ingestion completed successfully. Total chunks: %d",
            len(chunks),
        )

        return UploadResponse(
            status="SUCCESS",
            message=(
                f"Document uploaded successfully. " f"{len(chunks)} chunks created."
            ),
            document_name=file_name,
            document_path=str(pdf_path),
            total_chunks=len(chunks),
            version="1.0",
            ready_for_ingestion=True,
        )

    except Exception as e:

        logger.exception(
            "Document ingestion failed. File: %s",
            file_name,
        )

        return UploadResponse(
            status="FAILED",
            message=f"Document ingestion failed: {str(e)}",
            document_name=file_name,
            document_path=str(pdf_path),
            total_chunks=len(chunks),
            version="1.0",
            ready_for_ingestion=False,
        )
