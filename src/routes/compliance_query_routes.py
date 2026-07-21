"""
Compliance Query API routes.
"""

from fastapi import APIRouter, status

from src.schemas.compliance_request import ComplianceRequest
from src.schemas.compliance_response import ComplianceResponse
from src.services.complaince_service import compliance_service

from src.services.query_service import query_service

router = APIRouter(tags=["Compliance"])


@router.post(
    "/query",
    response_model=ComplianceResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Regulatory Knowledge Base",
    description="Answers compliance questions using retrieved regulatory documents.",
)
async def compliance_query(request: ComplianceRequest) -> ComplianceResponse:
    """
    Process a compliance query.
    Returns: ComplianceResponse
    """

    # print("Query :", request.query)
    return await compliance_service.process_query(request.query)
    # return await query_service(request.query)
