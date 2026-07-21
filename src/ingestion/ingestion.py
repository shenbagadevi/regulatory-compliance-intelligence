import os

import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.database import get_vector_store
from src.core.config import CHUNK_SIZE, CHUNK_OVERLAP
from src.schemas.compliance_response import UploadResponse, ComplianceResponse, Citation


def load_pdf(file_name, pdf_path):
    """
    Loads the PDF document.

    Args:
        pdf_path (str): Path of the PDF file.

    Returns:
        list: List of LangChain Document objects.
    """

    try:

        current_section = "N/A"
        current_regulation = "General"
        current_document_type = "General"

        loader = PyPDFLoader(pdf_path)

        docs = loader.load()

        #    # 2 metdata enrichment
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
        # print(docs)
        print(f"Document Loaded Successfully")
        print(f"Total Pages : {len(docs)}")
        return docs
    except Exception as e:
        print(f"PDF loading failed :{e}")
        raise


def split_documents(documents):
    """
    Splits the document into chunks using the
    project-specified chunking strategy.

    Returns:
        list: List of document chunks.
    """
    try:

        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=int(CHUNK_SIZE),
            chunk_overlap=int(CHUNK_OVERLAP),
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        chunks = splitter.split_documents(documents)

        print(f"Chunking Completed  Successfully")
        print(f"Total Chunks Created : {len(chunks)}")

        return chunks
    except Exception as e:
        print(f"ingestion.split_documents failed :{e}")
        raise


import re


def extract_section_metadata(text: str) -> dict:
    """
    Extract section information from page text.

    Example:
        ## SECTION 4: KYC & AML

    Returns:
    {
        "section": "SECTION 4: KYC & AML",
        "regulation_type": "RBI / PMLA",
        "document_type": "Guidelines"
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

    # section = f"SECTION {section_no}: {section_title}"
    section = f"SECTION {section_no}:"

    title = section_title.upper()

    # ------------------------
    # Regulation Type
    # ------------------------

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

    # ------------------------
    # Document Type
    # ------------------------

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

    Metadata required by project specification:
        - source
        - document_name
        - section_number
        - regulation_type
        - chunk_id
    """
    try:
        document_name = os.path.basename(pdf_path)

        for index, chunk in enumerate(chunks):

            chunk.metadata["document_name"] = document_name
            # fix unique chunk-id
            chunk.metadata["chunk_id"] = f"{document_name}_{index+1}"

            # Placeholder values.
            # These can later be extracted automatically
            # from headings inside regulatory documents.
            # chunk.metadata["section_number"] = extract_section(chunk.page_content)

            # chunk.metadata["regulation_type"] = extract_regulation_type(
            #    chunk.page_content
            # )

        return chunks
    except Exception as e:
        print(f"ingestion.enrich_metadata failed :{e}")
        raise


def store_chunks(chunks):
    """
    Store document chunks in PGVector.

    pre_delete_collection should be set to true during ingestion
    for drop exsting records from db table (if any)

    Same flag should be set to false during retreival process.

    """
    try:
        vector_store = get_vector_store(pre_delete_collection=True)
        vector_store.add_documents(chunks)

        print(f"{len(chunks)} chunks stored successfully.")
    except Exception as e:
        print(f"ingestion.store_chunks failed :{e}")
        raise


def ingest(file_name, pdf_path):
    """
    Complete ingestion pipeline.

    Steps:
        1. Load PDF
        2. Split into chunks
        3. Add metadata

    Args:
        file_name (str)
        pdf_path (str)


    Returns:
        list: Chunked documents
    """
    try:
        documents = load_pdf(file_name, pdf_path)

        chunks = split_documents(documents)

        chunks = enrich_metadata(chunks, pdf_path)

        store_chunks(chunks)

        # vectore_store = get_vector_store(collection_name="hr_support_desk")

        # vectore_store.add_documents(chunks)

        print("Document Ingestion Completed Successfully")

        # return chunks

        return UploadResponse(
            status="SUCCESS",
            message=f"Document uploaded successfully.{len(chunks)} Chunks created.",
            document_name=file_name,
            document_path=str(pdf_path),
            ready_for_ingestion=True,
        )
    except Exception as e:
        print(f"ingestion.ingest failed :{e}")
        return UploadResponse(
            status="Failed",
            message=f"Document uploaded failed.{e}",
            document_name=file_name,
            document_path=str(pdf_path),
            ready_for_ingestion=False,
        )


# ingest("data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf")


# test to run the ingestion part
# uv run tests/ingestion/ingestion.py
