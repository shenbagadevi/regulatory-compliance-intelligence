import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

# Load environment variables
load_dotenv()


# PostgreSQL Connection String
DB_CONNECTION = (
    f"postgresql+psycopg://"
    f"{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

# print("DB Connection String", DB_CONNECTION)


# Collection Name
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def get_embeddings():
    """
    Returns OpenAI Embedding model.
    """
    return OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL"), dimensions=1536)


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
