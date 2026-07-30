from langchain_core.documents import Document
from collections import defaultdict
from langchain_core.tools import tool
import re
from src.schemas.retrieval_store import set_documents
from src.core.config import *
from src.schemas.compliance_response import (
    RetrievalResult,
    RetrievedChunk,
)
from src.core.database import get_vector_store, get_connection
import logging
from src.core import logger

logger = logging.getLogger(__name__)


def vector_search(query: str, k: int = VECTOR_SEARCH_K):
    """
    Perform semantic similarity search.

    Args:
        query (str): User question.
        k (int): Number of documents to retrieve.

    Returns:
        List[Tuple[Document, float]]: Retrieved documents with similarity scores.
    """
    try:

        logger.info(
            "Starting vector search. Query='%s'",
            query,
        )

        vector_store = get_vector_store(pre_delete_collection=False)

        filters = extract_metadata_filters(query)

        if filters:

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
            "Semantic vector search completed successfully. Retrieved %d documents.",
            len(results),
        )

        return results

    except Exception:
        logger.exception("tools.vector_search failed.")
        raise


def keyword_search(query: str, limit: int = KEYWORD_SEARCH_K):
    """
    Performs PostgreSQL Full-Text Search on document chunks.

    Args:
        query (str): User search query.
        limit (int): Maximum number of documents to retrieve.

    Returns:
        List[Document]: Matching documents.
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

        documents = [
            Document(
                page_content=row[0],
                metadata=row[1],
            )
            for row in rows
        ]

        logger.info(
            "Keyword search completed successfully. Retrieved %d documents.",
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

                logger.debug("Database connection closed.")

            except Exception:

                logger.exception("Failed to close database connection.")


def rrf_rank(vector_docs, keyword_docs, k=60):
    """
    Rank documents using Reciprocal Rank Fusion (RRF).

    Args:
        vector_docs (List[Document]): Documents returned by vector search.
        keyword_docs (List[Document]): Documents returned by keyword search.
        k (int): RRF constant (default: 60).

    Returns:
        List[Document]: Ranked documents after fusion.
    """

    try:
        """
        logger.info(
            "Starting Reciprocal Rank Fusion. "
            "Vector documents=%d, Keyword documents=%d",
            len(vector_docs),
            len(keyword_docs),
        )
        """
        logger.info("Starting Reciprocal Rank Fusion. ")

        scores = defaultdict(float)
        doc_lookup = {}

        # Vector Search
        for rank, doc in enumerate(vector_docs, start=1):

            # Use unique chunk_id instead of page content
            key = doc.metadata.get("chunk_id")

            if not key:
                logger.warning("Skipping vector document without chunk_id.")
                continue

            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        # Keyword Search
        for rank, doc in enumerate(keyword_docs, start=1):

            key = doc.metadata.get("chunk_id")

            if not key:
                logger.warning("Skipping keyword document without chunk_id.")
                continue

            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        ranked_docs = [doc_lookup[key] for key, _ in ranked]

        logger.info(
            "RRF ranking completed successfully. Ranked %d documents.",
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

        # -------------------------
        # Vector Search
        # -------------------------
        vector_results = vector_search(
            query=query,
            k=vector_k,
        )

        vector_docs = []
        distance_map = {}

        for doc, score in vector_results:

            vector_docs.append(doc)

            chunk_id = doc.metadata.get("chunk_id")

            if chunk_id:
                distance_map[chunk_id] = score
            else:
                logger.warning("Vector search returned a document without chunk_id.")

        logger.info(
            "Vector search retrieved %d documents.",
            len(vector_docs),
        )

        # -------------------------
        # Keyword Search
        # -------------------------
        keyword_docs = keyword_search(
            query=query,
            limit=keyword_k,
        )

        # -------------------------
        # Reciprocal Rank Fusion
        # -------------------------
        ranked_docs = rrf_rank(
            vector_docs=vector_docs,
            keyword_docs=keyword_docs,
        )

        # -------------------------
        # Sort by latest source/version
        # -------------------------
        ranked_docs = sorted(
            ranked_docs,
            key=lambda doc: (
                doc.metadata.get("source_date", ""),
                doc.metadata.get("version", ""),
            ),
            reverse=True,
        )

        # -------------------------
        # Similarity Filtering
        # -------------------------
        filtered = []

        for doc in ranked_docs:

            chunk_id = doc.metadata.get("chunk_id")
            distance = distance_map.get(chunk_id)

            doc.metadata["vector_distance"] = distance

            # Keyword-only document
            if distance is None:

                filtered.append(doc)
                continue

            similarity = 1 / (1 + distance)

            if similarity >= MIN_SIMILARITY_SCORE:

                filtered.append(doc)

        logger.info(
            "Hybrid search completed successfully. "
            "Ranked=%d, Filtered=%d, Returned=%d",
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
    Extract metadata filters from the user query.

    Args:
        query (str): User query.

    Returns:
        dict: Metadata filters to be applied during vector search.
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
            filters if filters else "No filters applied",
        )

        return filters

    except Exception:

        logger.exception("tools.extract_metadata_filters failed.")

        raise


@tool
def semantic_retriever_tool(query: str):
    """
    Use when the answer depends on concepts,
    definitions, purposes, comparisons,
    or explanations.

    Args:
        query (str): User query.

    Returns:
        RetrievalResult: Structured retrieval result.
    """

    try:

        logger.info(
            "Executing semantic retriever tool. Query='%s'",
            query,
        )

        results = vector_search(query)

        docs = []

        for doc, score in results:

            doc.metadata["vector_distance"] = score

            docs.append(doc)

        set_documents(docs)

        retrieval_result = build_retrieval_result(docs)

        return retrieval_result

    except Exception:

        logger.exception("tools.semantic_retriever_tool failed.")

        raise


@tool
def keyword_retriever_tool(query: str):
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

        return build_retrieval_result(docs)

    except Exception:

        logger.exception("tools.keyword_retriever_tool failed.")

        raise


@tool
def hybrid_retriever_tool(query: str):
    """
    Use when both exact terminology and conceptual understanding
    are required, or when another retrieval tool returned
    insufficient information.

    Args:
        query (str): User query.

    Returns:
        RetrievalResult: Structured retrieval result.
    """

    try:

        docs = hybrid_search(query)

        set_documents(docs)

        retrieval_result = build_retrieval_result(docs)

        logger.info("Hybrid retriever completed successfully.")

        return retrieval_result

    except Exception:

        logger.exception("tools.hybrid_retriever_tool failed.")

        raise


def build_retrieval_result(docs) -> RetrievalResult:
    """
    Convert retrieved LangChain documents into a structured
    retrieval result for the LLM.

    Args:
        docs (List[Document]): Retrieved LangChain documents.

    Returns:
        RetrievalResult: Structured retrieval result.
    """

    try:

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

        return retrieval_result

    except Exception:

        logger.exception("tools.build_retrieval_result failed.")

        raise


def calculate_confidence(docs) -> float:
    """
    Calculate confidence based on:
    1. Average vector similarity
    2. Retrieval coverage
    3. Metadata quality

    Args:
        docs (List[Document]): Retrieved documents.

    Returns:
        float: Confidence score between 0.0 and 1.0.
    """

    try:

        if not docs:
            # logger.warning("No documents retrieved. Returning confidence score 0.0.")
            return 0.0
        distances = []

        for doc in docs:

            distance = doc.metadata.get("vector_distance")

            if distance is not None:
                distances.append(distance)

        # Keyword search returned documents but no vector scores
        if not distances:
            return 0.50

        avg_distance = sum(distances) / len(distances)

        # Convert distance into similarity
        similarity_score = 1 / (1 + avg_distance)

        # Retrieval completeness
        coverage_score = min(len(docs), 2) / 2

        # Metadata completeness
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
        """
        logger.info(
            "Confidence calculated successfully. "
            "Similarity=%.3f, Coverage=%.3f, Metadata=%.3f, Final=%.2f",
            similarity_score,
            coverage_score,
            metadata_score,
            confidence,
        )
        """

        return confidence

    except Exception:

        logger.exception("tools.calculate_confidence failed.")

        raise
