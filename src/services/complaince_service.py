import logging
import shutil
import uuid
import os

from pathlib import Path
from fastapi import UploadFile, HTTPException

from src.core import logger
from src.core.config import AppConfig
from src.ingestion.ingestion import ingest
from src.agents.rag_agent import (
    ask_compliance_agent,
    get_last_retrieved_documents,
)
from src.tools.tools import calculate_confidence
from src.agents.query_router import route_query
from src.schemas.retrieval_store import clear_documents
from src.schemas.compliance_response import (
    UploadResponse,
    ComplianceResponse,
    Citation,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Service class responsible for compliance-related operations.
    """

    async def upload_document(self, file: UploadFile) -> UploadResponse:
        """
        Upload and store a regulatory document.
        """
        try:
            logger.info("Document upload initiated.")

            if not file.filename:
                logger.warning("Upload request received without a filename.")
                raise HTTPException(400, "No file selected.")

            logger.info("Uploading file: %s", file.filename)

            extension = Path(file.filename).suffix.lower()

            if extension not in AppConfig.ALLOWED_FILE_EXTENSIONS:
                logger.warning(
                    "Unsupported file extension: %s",
                    extension,
                )
                raise HTTPException(
                    400,
                    "Only PDF documents are allowed.",
                )

            AppConfig.UPLOAD_DIRECTORY.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path = os.path.join(
                AppConfig.UPLOAD_DIRECTORY,
                file.filename,
            )

            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                logger.info(
                    "File saved successfully: %s",
                    file_path,
                )

            except Exception:
                logger.exception("Failed to save uploaded document.")
                raise HTTPException(
                    500,
                    "Unable to save uploaded document.",
                )

            upload_response = ingest(
                file.filename,
                file_path,
            )

            logger.info("Document uploaded and ingested successfully.")

            return upload_response

        except HTTPException:
            raise

        except Exception:
            logger.exception("Unexpected error during document upload.")
            raise

    async def process_query(
        self,
        query: str,
    ) -> ComplianceResponse:
        """
        Process a compliance question.
        """

        try:

            logger.info("Received compliance query.")

            clear_documents()

            handled, message = route_query(query)

            if handled:
                logger.info("Query handled by router.")

                return ComplianceResponse(
                    query=query,
                    answer=message,
                    citations=[],
                    rule_summary=[],
                    confidence_score=1.0,
                    disclaimer="",
                    langsmith_trace_id="",
                )

            logger.info("Invoking Compliance RAG Agent.")

            response = ask_compliance_agent(query)

            docs = get_last_retrieved_documents()

            logger.info(
                "Retrieved %s supporting documents.",
                len(docs),
            )

            compliance_response = ComplianceResponse(
                query=query,
                answer=response.answer,
                rule_summary=response.rule_summary,
                citations=build_citations(docs),
                confidence_score=calculate_confidence(docs),
                disclaimer=(
                    "This response was generated using an "
                    "AI-powered Retrieval-Augmented Generation "
                    "(RAG) system based on the uploaded "
                    "regulatory documents. Please verify the "
                    "information against the latest official "
                    "regulatory publications."
                ),
                langsmith_trace_id=str(uuid.uuid4()),
            )

            logger.info("Compliance query processed successfully.")

            return compliance_response

        except HTTPException:
            raise

        except Exception:
            logger.exception("Failed to process compliance query.")
            raise


def build_citations(docs):
    """
    Build citation objects from retrieved documents.
    """

    try:

        citations = []
        seen = set()

        logger.info(
            "Building citations from %s documents.",
            len(docs),
        )

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
                    document=metadata.get(
                        "document",
                        "N/A",
                    ),
                    section=metadata.get(
                        "section",
                        "N/A",
                    ),
                    page=metadata.get(
                        "page",
                        0,
                    )
                    + 1,
                    regulation_type=metadata.get(
                        "regulation_type",
                        "",
                    ),
                    version=metadata.get(
                        "version",
                        "1.0",
                    ),
                )
            )

        logger.info(
            "Generated %s citations.",
            len(citations),
        )

        return citations

    except Exception:
        logger.exception("Failed to build citations.")
        raise


compliance_service = ComplianceService()
