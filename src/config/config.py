"""
Application configuration module.

This module contains application-level constants used across
the Regulatory Compliance Intelligence System.

Keeping configuration in one place improves maintainability
and avoids hardcoded values throughout the application.
"""

from pathlib import Path


class AppConfig:
    """
    Centralized application configuration.
    """

    PROJECT_NAME: str = "Regulatory Compliance Intelligence System"

    API_VERSION: str = "v1"

    UPLOAD_DIRECTORY: Path = Path("data/regulatory_documents")

    ALLOWED_FILE_EXTENSIONS = {".pdf"}

    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024
