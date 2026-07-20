"""
Application entry point.
"""

from fastapi import FastAPI

from src.config.config import AppConfig
from src.routes.compliance_query_routes import router as compliance_router
from src.routes.document_routes import router as document_router
from src.routes.health_routes import router as health_router

app = FastAPI(
    title=AppConfig.PROJECT_NAME,
    version=AppConfig.API_VERSION,
    description="Regulatory Compliance Intelligence System",
)

app.include_router(health_router, prefix="/api/v1")

app.include_router(document_router, prefix="/api/v1")

app.include_router(compliance_router, prefix="/api/v1")
