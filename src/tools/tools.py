from langchain_core.documents import Document
from collections import defaultdict
from langchain_core.tools import tool
from src.core.config import VECTOR_SEARCH_K, KEYWORD_SEARCH_K, FINAL_SEARCH_K
from src.core.db import get_vector_store, get_connection
import psycopg


def vector_search(query: str, k: int = 5):
    """
    Perform semantic similarity search.

    Args:
        query (str): User question
        k (int): Number of documents to retrieve

    Returns:
        List[Document]
    """
    try:
        vector_store = get_vector_store(pre_delete_collection=False)

        results = vector_store.similarity_search(query=query, k=k)

        # print("vector search ended :", len(results))

        return results
    except Exception as e:
        print(f"tools.vector_search failed :{e}")
        raise


def keyword_search(query: str, limit: int = 5):
    """
    Performs PostgreSQL Full-Text Search on document chunks.
    """
    try:
        sql = """
            SELECT
                id,
                document,
                cmetadata
            FROM langchain_pg_embedding
            WHERE to_tsvector('english', document)
                @@ plainto_tsquery(%s)
            LIMIT %s;
        """

        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(sql, (query, limit))
            rows = cursor.fetchall()

        documents = []

        for row in rows:
            documents.append(Document(page_content=row[1], metadata=row[2]))

        return documents
    except Exception as e:
        print(f"tools.keyword_search failed :{e}")
        raise
    finally:
        conn.close()


def rrf_rank(vector_docs, keyword_docs, k=60):
    """
    Rank documents using Reciprocal Rank Fusion.
    """
    try:
        scores = defaultdict(float)
        doc_lookup = {}

        # Vector Search
        for rank, doc in enumerate(vector_docs, start=1):
            key = doc.page_content
            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        # Keyword Search
        for rank, doc in enumerate(keyword_docs, start=1):
            key = doc.page_content
            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [doc_lookup[key] for key, _ in ranked]
    except Exception as e:
        print(f"tools.rrf_rank failed :{e}")
        raise


def hybrid_search(
    query: str,
    vector_k: int = 5,
    keyword_k: int = 5,
    final_k: int = 5,
):
    """
    Performs Hybrid Search using:
    1. Vector Search
    2. Keyword Search
    3. Reciprocal Rank Fusion (RRF)

    Args:
        query (str): User query.
        vector_k (int): Number of documents from vector search.
        keyword_k (int): Number of documents from keyword search.
        final_k (int): Final number of documents to return.

    Returns:
        List[Document]: Ranked documents after fusion.
    """
    try:
        # Perform Vector Search
        vector_docs = vector_search(query=query, k=vector_k)

        # Perform Keyword Search
        keyword_docs = keyword_search(query=query, limit=keyword_k)

        # Merge & Rank using RRF
        ranked_docs = rrf_rank(vector_docs=vector_docs, keyword_docs=keyword_docs)

        # print(f"After RRF : {len(ranked_docs)}")

        # Return top documents
        return ranked_docs[:final_k]
    except Exception as e:
        print(f"tools.hybrid_search failed :{e}")
        raise


@tool
def compliance_retriever_tool(query: str) -> str:
    """
    Retrieves relevant compliance documents using Hybrid Search.
    """
    try:
        docs = hybrid_search(
            query=query,
            vector_k=VECTOR_SEARCH_K,
            keyword_k=KEYWORD_SEARCH_K,
            final_k=FINAL_SEARCH_K,
        )

        if not docs:
            return "No relevant documents found."

        context = []

        for doc in docs:
            context.append(doc.page_content)

        return "\n\n".join(context)
    except Exception as e:
        print(f"tools.compliance_retriever_tool failed :{e}")
        raise
