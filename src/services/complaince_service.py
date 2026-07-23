"""
Business service for the Regulatory Compliance Intelligence System.

This module contains the core business logic for:
1. Uploading regulatory documents.
2. Validating uploaded files.
3. Processing compliance queries.
4. Preparing integration with the RAG pipeline.
"""

from src.schemas.compliance_response import UploadResponse, ComplianceResponse, Citation
import logging, shutil, uuid
from fastapi import FastAPI, UploadFile, HTTPException
from pathlib import Path

# from src.core.config import AppConfig
from src.core.config import AppConfig
from src.ingestion.ingestion import ingest
from src.agents.rag_agent import ask_compliance_agent
from src.tools.tools import hybrid_search
from src.core.config import FINAL_SEARCH_K, KEYWORD_SEARCH_K, VECTOR_SEARCH_K
from src.agents.query_router import route_query

import os

# Configure application logger
logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Service class responsible for compliance-related operations.

    This class encapsulates the business logic and keeps the
    FastAPI route handlers lightweight.
    """

    async def upload_document(self, file: UploadFile) -> UploadResponse:
        """
        Upload and store a regulatory document.

        Workflow
        --------
        1. Validate uploaded file.
        2. Create upload directory if missing.
        3. Save file locally.
        4. Return upload metadata.
        """
        logger.info("Uploading document: %s", file.filename)

        if not file.filename:
            raise HTTPException(400, "No file selected.")
        extension = Path(file.filename).suffix.lower()

        if extension not in AppConfig.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(400, "Only PDF documents are allowed.")
        AppConfig.UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

        file_path = os.path.join(AppConfig.UPLOAD_DIRECTORY, file.filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as ex:
            logger.exception("Failed to save uploaded file.")

            raise HTTPException(500, "Unable to save uploaded document.") from ex

        # print(file.filename, " --", file_path)
        # ingest("data/Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf")
        # print("before calling ingestion method")
        UploadResponse = ingest(file.filename, file_path)
        logger.info("Document saved successfully.")
        return UploadResponse

        """
        return UploadResponse(
            status="SUCCESS",
            message="Document uploaded successfully.",
            document_name=file.filename,
            document_path=str(file_path),
            ready_for_ingestion=True,
        )"""

    async def process_query(self, query: str) -> ComplianceResponse:
        """
        Process a compliance question.
        Retrieve relevant clauses and generate response.
        """
        logger.info("Received compliance query.")
        handled, message = route_query(query)

        if handled:
            return ComplianceResponse(
                query=query,
                answer=message,
                citations=[],
                rule_summary=[],
                confidence_score=1.0,
                disclaimer="",
                langsmith_trace_id="",
            )

        response = ask_compliance_agent(query)
        response.query = query

        response.langsmith_trace_id = str(uuid.uuid4())

        if not response.disclaimer:
            response.disclaimer = (
                "This response was generated using an AI-powered "
                "Retrieval-Augmented Generation (RAG) system based on "
                "the uploaded regulatory documents. Please verify the "
                "information against the latest official regulatory publications."
            )

        return response

    def build_citations(self, docs):
        citations = []
        seen = set()

        for doc in docs:
            metadata = doc.metadata

            key = (
                metadata.get("document"),
                metadata.get("section"),
                metadata.get("page"),
            )

            if key in seen:
                continue

            seen.add(key)

            citations.append(
                Citation(
                    document=metadata.get("document", "N/A"),
                    section=metadata.get("section", "N/A"),
                    page=metadata.get("page", 0) + 1,  # convert to 1-based page
                )
            )

        return citations


compliance_service = ComplianceService()
