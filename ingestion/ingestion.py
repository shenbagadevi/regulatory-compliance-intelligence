import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.db import get_vector_store


def load_pdf(pdf_path):
    """
    Loads the PDF document.

    Args:
        pdf_path (str): Path of the PDF file.

    Returns:
        list: List of LangChain Document objects.
    """

    loader = PyPDFLoader(pdf_path)

    docs = loader.load()

    #    # 2 metdata enrichment
    #    for doc in docs:
    #        doc.metadata.update(
    #            {
    #                "source": file_path,
    #                "document_extension": "pdf",
    #                "page": doc.metadata.get("page"),
    #                "last_updated": os.path.getmtime(file_path),
    #            }
    #        )
    # print(docs)
    print(f"Document Loaded Successfully")
    print(f"Total Pages : {len(docs)}")

    return docs


def split_documents(documents):
    """
    Splits the document into chunks using the
    project-specified chunking strategy.

    Returns:
        list: List of document chunks.
    """

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=int(os.getenv("CHUNK_SIZE", 512)),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 100)),
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    print(f"Chunking Completed  Successfully")
    print(f"Total Chunks Created : {len(chunks)}")

    return chunks


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

    document_name = os.path.basename(pdf_path)

    for index, chunk in enumerate(chunks):

        chunk.metadata["document_name"] = document_name

        chunk.metadata["chunk_id"] = index + 1

        # Placeholder values.
        # These can later be extracted automatically
        # from headings inside regulatory documents.
        chunk.metadata["section_number"] = "Unknown"

        chunk.metadata["regulation_type"] = "General"

    return chunks


def store_chunks(chunks):
    """
    Store document chunks in PGVector.

    pre_delete_collection should be set to true during ingestion
    for drop exsting records from db table (if any)

    Same flag should be set to false during retreival process.

    """

    vector_store = get_vector_store(pre_delete_collection=True)
    vector_store.add_documents(chunks)

    print(f"{len(chunks)} chunks stored successfully.")


def ingest(pdf_path):
    """
    Complete ingestion pipeline.

    Steps:
        1. Load PDF
        2. Split into chunks
        3. Add metadata

    Args:
        pdf_path (str)

    Returns:
        list: Chunked documents
    """

    documents = load_pdf(pdf_path)

    chunks = split_documents(documents)

    chunks = enrich_metadata(chunks, pdf_path)

    store_chunks(chunks)

    # vectore_store = get_vector_store(collection_name="hr_support_desk")

    # vectore_store.add_documents(chunks)

    print("Document Ingestion Completed Successfully")

    return chunks


ingest("data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf")


# test to run the ingestion part
# uv run /ingestion/ingestion.py
