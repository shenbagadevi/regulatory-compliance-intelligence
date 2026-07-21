"""
Request schema definitions.

This module contains request models used by the Regulatory
Compliance Intelligence System API.
"""

from pydantic import BaseModel, Field


class ComplianceRequest(BaseModel):
    """
    Request model for compliance-related queries.
        query:
            Natural language question submitted by the user.
    """

    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Compliance question to search in the regulatory knowledge base.",
        # examples=["What is the maximum LTV ratio for gold loans?"],
        examples=["What are the KYC requirements for high-risk customer as per SEBI?"],
    )
