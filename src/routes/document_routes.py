"""
Document API routes.
"""

from fastapi import APIRouter, UploadFile, File, status
from src.schemas.compliance_response import UploadResponse
from src.services.complaince_service import compliance_service

router = APIRouter(prefix="/documents", tags=["Documents"])

# localhost:8000/upload
# localhost:8000/api/v1/documents/upload


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Regulatory Document",
    description="Uploads a regulatory PDF document to the knowledge base.",
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a regulatory document.
    Returns upload response
    """
    return await compliance_service.upload_document(file)
