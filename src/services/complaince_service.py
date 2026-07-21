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

import os

# Configure application logger
logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Service class responsible for compliance-related operations.

    This class encapsulates the business logic and keeps the
    FastAPI route handlers lightweight.
    """

    SMALL_TALK = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "who are you",
        "what can you do",
        "thank you",
        "thanks",
        "bye",
    }

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
        logger.info("Received compliance query.")
        if self.is_small_talk(query):
            return ComplianceResponse(
                query=query,
                answer=self.get_small_talk_response(query),
                rule_summary=[],
                citations=[],
                confidence_score=1.0,
                disclaimer="",
                langsmith_trace_id=str(uuid.uuid4()),
            )

        docs = hybrid_search(
            query=query,
            vector_k=VECTOR_SEARCH_K,
            keyword_k=KEYWORD_SEARCH_K,
            final_k=FINAL_SEARCH_K,
        )
        citations = self.build_citations(docs)
        confidence = self.calculate_confidence(docs)
        answer = ask_compliance_agent(query)
        # print("answer 1 here  : ", answer1)
        # confidence = min(len(docs) / FINAL_SEARCH_K, 1.0)
        return ComplianceResponse(
            query=query,
            answer=answer,
            citations=citations,
            rule_summary=[],
            confidence_score=confidence,
            disclaimer=(
                "This response was generated using an AI-powered "
                "Retrieval-Augmented Generation (RAG) system based on "
                "the uploaded regulatory documents. "
                "Users should verify information against official "
                "regulatory publications before making decisions."
            ),
            langsmith_trace_id=str(uuid.uuid4()),
        )

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

    def calculate_confidence(self, docs):
        """
        Calculate confidence based on:
        1. Average vector similarity
        2. Number of retrieved documents
        """

        if not docs:
            return 0.0
        distances = []

        for doc in docs:
            distance = doc.metadata.get("vector_distance")

            if distance is not None:
                distances.append(distance)

        # If keyword search returned documents but no vector scores
        if not distances:
            return 0.50

        avg_distance = sum(distances) / len(distances)

        # Convert distance into similarity
        similarity_score = 1 / (1 + avg_distance)

        # Retrieval completeness
        retrieval_score = len(docs) / FINAL_SEARCH_K

        # Weighted confidence
        confidence = similarity_score * 0.8 + retrieval_score * 0.2

        return round(min(confidence, 1.0), 2)

    def is_small_talk(self, query: str) -> bool:
        query = query.lower().strip()
        return query in self.SMALL_TALK

    def get_small_talk_response(self, query: str):
        query = query.lower().strip()
        if "hi" in query or "hello" in query or "hey" in query:
            return "Hello! How can I assist you with regulatory compliance today?"

        if "how are you" in query:
            return "I'm doing well, thank you! How can I help you with regulatory compliance?"

        if "who are you" in query:
            return (
                "I am an AI-powered Regulatory Compliance Assistant that helps "
                "answer questions using the uploaded regulatory documents."
            )

        if "what can you do" in query:
            return (
                "I can answer regulatory compliance questions, summarize "
                "requirements, and provide supporting document citations."
            )

        if "thank" in query:
            return (
                "You're welcome! Let me know if you have another compliance question."
            )

        if "bye" in query:
            return "Goodbye! Have a great day."

        return "Hello! How can I help you today?"


compliance_service = ComplianceService()
