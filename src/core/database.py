import logging

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
import psycopg

# Initialize logging configuration
from src.core import logger

from src.core.config import (
    COLLECTION_NAME,
    DB_CONNECTION,
    EMBEDDING_MODEL,
    DB_CONNECTION_FTS,
)

# Module logger
logger = logging.getLogger(__name__)


def get_embeddings():
    """
    Returns OpenAI Embedding model.
    """
    try:
        # logger.info("Initializing OpenAI embedding model.")

        embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            dimensions=1536,
        )

        # logger.info("OpenAI embedding model initialized successfully.")

        return embeddings

    except Exception:
        logger.exception("Failed to initialize OpenAI embedding model.")
        raise


def get_vector_store(pre_delete_collection: bool = False):
    """
    Returns PGVector object.
    """
    try:
        """
        logger.info(
            "Initializing PGVector. Collection=%s, PreDelete=%s",
            COLLECTION_NAME,
            pre_delete_collection,
        )

        """
        vector_store = PGVector(
            embeddings=get_embeddings(),
            collection_name=COLLECTION_NAME,
            connection=DB_CONNECTION,
            use_jsonb=True,
            pre_delete_collection=pre_delete_collection,
        )

        # logger.info("PGVector initialized successfully.")

        return vector_store

    except Exception:
        logger.exception("Failed to initialize PGVector.")
        raise


def get_connection():
    """
    Returns a PostgreSQL connection.
    Used for Full-Text Search and other SQL queries.
    """
    try:
        # logger.info("Creating PostgreSQL database connection.")

        connection = psycopg.connect(DB_CONNECTION_FTS)

        # logger.info("PostgreSQL connection established successfully.")

        return connection

    except psycopg.Error:
        logger.exception("Failed to connect to PostgreSQL database.")
        raise

    except Exception:
        logger.exception("Unexpected error while creating PostgreSQL connection.")
        raise
