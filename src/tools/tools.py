from collections import defaultdict
import logging
import re

from langchain_core.documents import Document
from langchain_core.tools import tool

# Initialize logging configuration
from src.core import logger

from src.core.config import *
from src.core.database import get_connection, get_vector_store
from src.schemas.compliance_response import (
    RetrievalResult,
    RetrievedChunk,
)
from src.schemas.retrieval_store import set_documents

logger = logging.getLogger(__name__)


def vector_search(query: str, k: int = VECTOR_SEARCH_K):
    """
    Perform semantic similarity search.

    Args:
        query (str): User question
        k (int): Number of documents to retrieve

    Returns:
        List[Document]
    """

    try:

        logger.info(
            "Starting semantic vector search. Query='%s'",
            query,
        )

        vector_store = get_vector_store(pre_delete_collection=False)

        filters = extract_metadata_filters(query)

        if filters:

            logger.info(
                "Applying metadata filters: %s",
                filters,
            )

            results = vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filters,
            )

        else:

            results = vector_store.similarity_search_with_score(
                query=query,
                k=k,
            )

        logger.info(
            "Semantic search completed successfully. Retrieved %s documents.",
            len(results),
        )

        return results

    except Exception:

        logger.exception("tools.vector_search failed.")

        raise


def keyword_search(query: str, limit: int = KEYWORD_SEARCH_K):
    """
    Performs PostgreSQL Full-Text Search on document chunks.
    """

    conn = None

    try:

        logger.info(
            "Starting keyword search. Query='%s'",
            query,
        )

        sql = """
                SELECT
                    document,
                    cmetadata,

                    ts_rank(
                        to_tsvector(
                            'english',
                            document ||
                            ' ' ||
                            COALESCE(cmetadata->>'section','') ||
                            ' ' ||
                            COALESCE(cmetadata->>'regulation_type','') ||
                            ' ' ||
                            COALESCE(cmetadata->>'document_name','')
                        ),
                        plainto_tsquery(%s)
                    ) AS rank

                FROM langchain_pg_embedding

                WHERE

                to_tsvector(
                    'english',
                    document ||
                    ' ' ||
                    COALESCE(cmetadata->>'section','') ||
                    ' ' ||
                    COALESCE(cmetadata->>'regulation_type','') ||
                    ' ' ||
                    COALESCE(cmetadata->>'document_name','')
                )
                @@ plainto_tsquery(%s)

                ORDER BY rank DESC

                LIMIT %s;
        """

        conn = get_connection()

        with conn.cursor() as cursor:

            cursor.execute(
                sql,
                (
                    query,
                    query,
                    limit,
                ),
            )

            rows = cursor.fetchall()

        documents = []

        for row in rows:

            documents.append(
                Document(
                    page_content=row[0],
                    metadata=row[1],
                )
            )

        logger.info(
            "Keyword search completed successfully. Retrieved %s documents.",
            len(documents),
        )

        return documents

    except Exception:

        logger.exception("tools.keyword_search failed.")

        raise

    finally:

        if conn:

            try:
                conn.close()

                logger.debug("PostgreSQL connection closed.")

            except Exception:

                logger.exception("Failed to close PostgreSQL connection.")


def rrf_rank(vector_docs, keyword_docs, k=60):
    """
    Rank documents using Reciprocal Rank Fusion.
    """

    try:

        logger.info(
            "Starting Reciprocal Rank Fusion (RRF). " "Vector Docs=%s, Keyword Docs=%s",
            len(vector_docs),
            len(keyword_docs),
        )

        scores = defaultdict(float)
        doc_lookup = {}

        # Vector Search
        for rank, doc in enumerate(vector_docs, start=1):

            # RRF should use unique chunk ID instead of page_content
            key = doc.metadata.get("chunk_id")

            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        # Keyword Search
        for rank, doc in enumerate(keyword_docs, start=1):

            key = doc.metadata.get("chunk_id")

            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        ranked_docs = [doc_lookup[key] for key, _ in ranked]

        logger.info(
            "RRF completed successfully. Ranked %s documents.",
            len(ranked_docs),
        )

        return ranked_docs

    except Exception:

        logger.exception("tools.rrf_rank failed.")

        raise


def hybrid_search(
    query: str,
    vector_k: int = VECTOR_SEARCH_K,
    keyword_k: int = KEYWORD_SEARCH_K,
    final_k: int = FINAL_SEARCH_K,
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

        logger.info(
            "Starting hybrid search. Query='%s'",
            query,
        )

        # Perform Vector Search
        # vector_docs = vector_search(query=query, k=vector_k)
        vector_results = vector_search(
            query=query,
            k=vector_k,
        )

        vector_docs = []
        distance_map = {}

        for doc, score in vector_results:

            vector_docs.append(doc)

            # Use chunk_id because it is unique
            # retrieve/stores not only the last document distance
            chunk_id = doc.metadata.get("chunk_id")
            distance_map[chunk_id] = score

        logger.info(
            "Vector search returned %s documents.",
            len(vector_docs),
        )

        # Perform Keyword Search
        keyword_docs = keyword_search(
            query=query,
            limit=keyword_k,
        )

        logger.info(
            "Keyword search returned %s documents.",
            len(keyword_docs),
        )

        # Merge & Rank using RRF
        ranked_docs = rrf_rank(
            vector_docs=vector_docs,
            keyword_docs=keyword_docs,
        )

        ranked_docs = sorted(
            ranked_docs,
            key=lambda doc: (
                doc.metadata.get("source_date", ""),
                doc.metadata.get("version", ""),
            ),
            reverse=True,
        )

        filtered = []

        for doc in ranked_docs:

            chunk_id = doc.metadata.get("chunk_id")
            distance = distance_map.get(chunk_id)

            doc.metadata["vector_distance"] = distance

            if distance is None:

                filtered.append(doc)
                continue

            similarity = 1 / (1 + distance)

            if similarity >= MIN_SIMILARITY_SCORE:

                filtered.append(doc)

        logger.info(
            "Hybrid search completed successfully. "
            "Retrieved=%s, Filtered=%s, Returned=%s",
            len(ranked_docs),
            len(filtered),
            min(len(filtered), final_k),
        )

        return filtered[:final_k]

    except Exception:

        logger.exception("tools.hybrid_search failed.")

        raise


def extract_metadata_filters(query: str):
    """
    Extract metadata filters from user query.
    """

    try:

        logger.info("Extracting metadata filters from query.")

        filters = {}

        query_upper = query.upper()

        if "RBI" in query_upper:
            filters["regulation_type"] = "RBI"

        elif "SEBI" in query_upper:
            filters["regulation_type"] = "SEBI"

        elif "BASEL" in query_upper:
            filters["regulation_type"] = "Basel III"

        elif "AML" in query_upper:
            filters["regulation_type"] = "RBI / PMLA"

        logger.info(
            "Metadata filters extracted: %s",
            filters,
        )

        return filters

    except Exception:

        logger.exception("tools.extract_metadata_filters failed.")

        raise


@tool
def semantic_retriever_tool(
    query: str,
):
    """
    Use when the answer depends on concepts,
    definitions, purposes, comparisons,
    or explanations.
    """

    try:

        logger.info("Executing semantic retriever tool.")

        results = vector_search(query)

        docs = []

        for doc, score in results:

            doc.metadata["vector_distance"] = score

            docs.append(doc)

        set_documents(docs)

        logger.info(
            "Semantic retriever returned %s documents.",
            len(docs),
        )

        return build_retrieval_result(docs)

    except Exception:

        logger.exception("tools.semantic_retriever_tool failed.")

        raise


@tool
def keyword_retriever_tool(
    query: str,
):
    """
    Use when the question contains exact
    regulation names, sections,
    clauses, circular numbers,
    or document titles.
    """

    try:

        logger.info("Executing keyword retriever tool.")

        docs = keyword_search(query)

        set_documents(docs)

        logger.info(
            "Keyword retriever returned %s documents.",
            len(docs),
        )

        return build_retrieval_result(docs)

    except Exception:

        logger.exception("tools.keyword_retriever_tool failed.")

        raise


@tool
def hybrid_retriever_tool(
    query: str,
):
    """
    Use when both exact terminology and conceptual understanding
    are required, or when another retrieval tool returned
    insufficient information.
    """

    try:

        logger.info("Executing hybrid retriever tool.")

        docs = hybrid_search(query)

        set_documents(docs)

        logger.info(
            "Hybrid retriever returned %s documents.",
            len(docs),
        )

        return build_retrieval_result(docs)

    except Exception:

        logger.exception("tools.hybrid_retriever_tool failed.")

        raise


def build_retrieval_result(
    docs,
) -> RetrievalResult:
    """
    Convert retrieved LangChain documents into a
    structured retrieval result.
    """

    try:

        logger.info(
            "Building retrieval result for %s documents.",
            len(docs),
        )

        chunks = []

        for doc in docs:

            chunks.append(
                RetrievedChunk(
                    content=doc.page_content[:MAX_CONTEXT],
                    document=doc.metadata.get(
                        "document_name",
                        doc.metadata.get("document", ""),
                    ),
                    section=doc.metadata.get(
                        "section",
                        "",
                    ),
                    page=doc.metadata.get(
                        "page",
                        0,
                    )
                    + 1,
                    vector_distance=doc.metadata.get(
                        "vector_distance",
                    ),
                )
            )

        retrieval_result = RetrievalResult(
            chunks=chunks,
            confidence=calculate_confidence(docs),
            source_documents=docs,
        )

        logger.info("Retrieval result built successfully.")

        return retrieval_result

    except Exception:

        logger.exception("tools.build_retrieval_result failed.")

        raise


def calculate_confidence(docs):
    """
    Calculate confidence score.
    """

    try:

        logger.info("Calculating confidence score.")

        if not docs:
            return 0.0

        distances = []

        for doc in docs:

            distance = doc.metadata.get("vector_distance")

            if distance is not None:
                distances.append(distance)

        # If keyword search returned documents but no vector scores
        if not distances:

            logger.info("No vector distances available. Returning default confidence.")

            return 0.50

        avg_distance = sum(distances) / len(distances)

        similarity_score = 1 / (1 + avg_distance)

        coverage_score = min(len(docs), 2) / 2

        metadata_score = sum(
            1 for doc in docs if doc.metadata.get("section") != "N/A"
        ) / len(docs)

        confidence = (
            similarity_score * 0.60 + coverage_score * 0.20 + metadata_score * 0.20
        )

        confidence = round(
            min(confidence, 1.0),
            2,
        )

        logger.info(
            "Confidence score calculated: %.2f",
            confidence,
        )

        return confidence

    except Exception:

        logger.exception("tools.calculate_confidence failed.")

        raise
