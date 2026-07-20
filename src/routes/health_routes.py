"""
Health check routes.
"""

from fastapi import APIRouter

from src.config.config import AppConfig
from src.schemas.compliance_response import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health", response_model=HealthResponse, summary="Application Health Check"
)
async def health_check() -> HealthResponse:
    """
    Check application health.
    Returns: HealthResponse
    """
    return HealthResponse(
        status="UP",
        application=AppConfig.PROJECT_NAME,
        version=AppConfig.API_VERSION,
    )
