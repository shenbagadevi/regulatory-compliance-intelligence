"""
Response schema definitions.

This module contains response models returned by the
Regulatory Compliance Intelligence System API.
"""

from typing import List
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    Represents a supporting citation for the generated answer.

        document:
            Name of the regulatory document.
        section:
            Section within the document.
        page:
            Page number where the answer was found.
    """

    document: str = Field(
        ...,
        description="Source document name.",
        examples=["Capstone_Project_1_Regulatory_Compliance_System_FAQ.pdf"],
    )

    section: str = Field(
        ...,
        description="Document section containing the relevant clause.",
        examples=["SECTION 1: RBI Gold Loan Guidelines"],
    )

    page: int = Field(
        ...,
        ge=1,
        description="Page number in the source document.",
        examples=[1],
    )


class RetrievedChunk(BaseModel):
    """
    Represents a single document chunk returned by the retrieval layer.

    This model is exchanged between retrieval tools and the LLM.
    It contains both the chunk content and its associated metadata.
    """

    content: str

    document: str

    section: str

    page: int

    vector_distance: float | None = None


class RetrievalResult(BaseModel):
    """
    Represents the output returned by a retrieval tool.

    The retrieval layer computes the confidence score based on
    retrieval quality and returns the retrieved chunks for
    answer generation.
    """

    chunks: List[RetrievedChunk]

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Retrieval confidence score.",
    )


class ComplianceResponse(BaseModel):
    """
    Response model for compliance queries.

        answer:
            Grounded answer generated from retrieved documents.

        citations:
            Supporting document references.

        rule_summary:
            Key compliance rules extracted from the answer.

        confidence_score:
            Confidence score between 0 and 1.

        disclaimer:
            Regulatory disclaimer.

        langsmith_trace_id:
            Trace identifier for debugging and monitoring.
    """

    query: str

    answer: str

    citations: List[Citation]

    rule_summary: List[str]

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the generated answer.",
    )

    disclaimer: str

    langsmith_trace_id: str


class UploadResponse(BaseModel):
    """
    Response model returned after successful document upload.

        status:
            Upload status.

        message:
            Upload result message.

        document_name:
            Uploaded file name.

        document_path:
            Location where the document is stored.

        ready_for_ingestion:
            Indicates whether the file is ready for the RAG ingestion pipeline.
    """

    status: str

    message: str

    document_name: str

    document_path: str

    ready_for_ingestion: bool


class HealthResponse(BaseModel):
    """
    Response model for the health endpoint.
    """

    status: str

    application: str

    version: str
