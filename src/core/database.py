import os

# from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from src.core.config import (
    COLLECTION_NAME,
    DB_CONNECTION,
    EMBEDDING_MODEL,
    DB_CONNECTION_FTS,
)
import psycopg

# Load environment variables
# load_dotenv()


def get_embeddings():
    """
    Returns OpenAI Embedding model.
    """
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=1536)


def get_vector_store(pre_delete_collection: bool = False):
    """
    Returns PGVector object.
    """

    vector_store = PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
        use_jsonb=True,
        pre_delete_collection=pre_delete_collection,
    )

    return vector_store


def get_connection():
    """
    Returns a PostgreSQL connection.
    Used for Full-Text Search and other SQL queries.
    """

    return psycopg.connect(DB_CONNECTION_FTS)
