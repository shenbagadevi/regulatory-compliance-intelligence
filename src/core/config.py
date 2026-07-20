"""
Application configuration.

Loads all environment variables from the .env file and exposes them
as Python constants for use throughout the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------------------------------
# OpenAI Configuration
# -------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai:gpt-5.5")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# -------------------------------------------------
# Database Configuration
# -------------------------------------------------

# PostgreSQL Connection String
DB_CONNECTION = (
    f"postgresql+psycopg://"
    f"{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# PostgreSQL Connection String for Full Text search
DB_CONNECTION_FTS = DB_CONNECTION.replace("postgresql+psycopg://", "postgresql://")

# Collection Name in PGVector DB
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "regulatory_docs")


# -------------------------------------------------
# Document Chunking
# -------------------------------------------------

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


# -------------------------------------------------
# Search Configuration
# -------------------------------------------------

VECTOR_SEARCH_K = int(os.getenv("VECTOR_SEARCH_K", "5"))
KEYWORD_SEARCH_K = int(os.getenv("KEYWORD_SEARCH_K", "5"))
FINAL_SEARCH_K = int(os.getenv("FINAL_SEARCH_K", "5"))

# -------------------------------------------------
# File Storage
# -------------------------------------------------

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

# -------------------------------------------------
# Validation
# -------------------------------------------------

REQUIRED_SETTINGS = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "DATABASE_URL": DB_CONNECTION,
}

missing = [key for key, value in REQUIRED_SETTINGS.items() if not value]

if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
