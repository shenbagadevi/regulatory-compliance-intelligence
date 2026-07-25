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


def vector_search(query: str, k: int = VECTOR_SEARCH_K):
    """
    Perform semantic similarity search.
        query (str): User question
        k (int): Number of documents to retrieve
    Returns: List[Document]
    """
    try:
        vector_store = get_vector_store(pre_delete_collection=False)

        # results = vector_store.similarity_search(query=query, k=k)
        # results = vector_store.similarity_search_with_score(query=query, k=k)
        filters = extract_metadata_filters(query)

        if filters:

            results = vector_store.similarity_search_with_score(
                query=query, k=k, filter=filters
            )

        else:

            results = vector_store.similarity_search_with_score(query=query, k=k)
        # print("vector search ended :", len(results))

        return results
    except Exception as e:
        print(f"tools.vector_search failed :{e}")
        raise


def keyword_search(query: str, limit: int = KEYWORD_SEARCH_K):
    """
    Performs PostgreSQL Full-Text Search on document chunks.
    """
    try:
        # Improved query to perform keyword search better with rank
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
            cursor.execute(sql, (query, query, limit))
            rows = cursor.fetchall()

        documents = []

        for row in rows:
            documents.append(Document(page_content=row[0], metadata=row[1]))

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
            # RRF should use unique chunk ID instead of page_content
            key = doc.metadata.get("chunk_id")
            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        # Keyword Search
        for rank, doc in enumerate(keyword_docs, start=1):
            key = doc.metadata.get("chunk_id")
            scores[key] += 1 / (k + rank)
            doc_lookup[key] = doc

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [doc_lookup[key] for key, _ in ranked]
    except Exception as e:
        print(f"tools.rrf_rank failed :{e}")
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
        # Perform Vector Search
        # vector_docs = vector_search(query=query, k=vector_k)
        vector_results = vector_search(query=query, k=vector_k)

        vector_docs = []
        distance_map = {}

        for doc, score in vector_results:
            vector_docs.append(doc)
            # Use chunk_id because it is unique
            # comment: retrieve/stores not only the last documents distance
            chunk_id = doc.metadata.get("chunk_id")
            distance_map[chunk_id] = score

        # Perform Keyword Search
        keyword_docs = keyword_search(query=query, limit=keyword_k)

        # Merge & Rank using RRF
        ranked_docs = rrf_rank(vector_docs=vector_docs, keyword_docs=keyword_docs)
        ranked_docs = sorted(
            ranked_docs,
            key=lambda doc: (
                doc.metadata.get("source_date", ""),
                doc.metadata.get("version", ""),
            ),
            reverse=True,
        )
        # print(f"After RRF : {len(ranked_docs)}")
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

        # Return top documents
        return filtered[:final_k]
    except Exception as e:
        print(f"tools.hybrid_search failed :{e}")
        raise


def extract_metadata_filters(query: str):

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

    return filters


@tool
def semantic_retriever_tool(
    query: str,
):
    """
    Use when the answer depends on concepts,
    definitions, purposes, comparisons,
    or explanations.
    """

    results = vector_search(query)

    docs = []

    for doc, score in results:

        doc.metadata["vector_distance"] = score

        docs.append(doc)

    set_documents(docs)
    return build_retrieval_result(docs)


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

    docs = keyword_search(query)
    set_documents(docs)
    return build_retrieval_result(docs)


@tool
def hybrid_retriever_tool(
    query: str,
):
    """
    Use when both exact terminology and conceptual understanding are required,
    or when another retrieval tool returned insufficient information.
    """

    docs = hybrid_search(query)
    set_documents(docs)
    return build_retrieval_result(docs)


def build_retrieval_result(docs) -> RetrievalResult:
    """
    Convert retrieved LangChain documents into a structured
    retrieval result for the LLM.
    """

    chunks = []

    for doc in docs:
        chunks.append(
            RetrievedChunk(
                content=doc.page_content[:MAX_CONTEXT],
                document=doc.metadata.get(
                    "document_name", doc.metadata.get("document", "")
                ),
                section=doc.metadata.get("section", ""),
                page=doc.metadata.get("page", 0) + 1,
                vector_distance=doc.metadata.get("vector_distance"),
            )
        )

    return RetrievalResult(
        chunks=chunks,
        confidence=calculate_confidence(docs),
        source_documents=docs,
    )


def calculate_confidence(docs):
    """
    Calculate confidence based on:
    1. Average vector similarity
    2. Number of retrieved documents
    """

    if not docs:
        return 0.0
    distances = []

    for doc in docs:
        distance = doc.metadata.get("vector_distance")

        if distance is not None:
            distances.append(distance)

    # If keyword search returned documents but no vector scores
    if not distances:
        return 0.50

    avg_distance = sum(distances) / len(distances)

    # Convert distance into similarity
    similarity_score = 1 / (1 + avg_distance)

    # Retrieval completeness
    retrieval_score = len(docs) / FINAL_SEARCH_K

    # Weighted confidence
    # confidence = similarity_score * 0.8 + retrieval_score * 0.2
    coverage_score = min(len(docs), 2) / 2

    metadata_score = sum(
        1 for doc in docs if doc.metadata.get("section") != "N/A"
    ) / len(docs)

    confidence = similarity_score * 0.60 + coverage_score * 0.20 + metadata_score * 0.20

    return round(min(confidence, 1.0), 2)


# @tool
# def compliance_retriever_tool(query: str) -> str:
#     """
#     Retrieves relevant compliance documents using Hybrid Search.
#     """
#     try:
#         docs = hybrid_search(
#             query=query,
#             vector_k=VECTOR_SEARCH_K,
#             keyword_k=KEYWORD_SEARCH_K,
#             final_k=FINAL_SEARCH_K,
#         )

#         if not docs:
#             return "No relevant documents found."

#         context = []

#         for doc in docs:
#             # metadata in LLMContext
#             context.append(f"""
#             Document: {doc.metadata.get('document')}
#             Section: {doc.metadata.get('section')}
#             Page: {doc.metadata.get('page')}

#             Content:
#             {doc.page_content}
#             """)

#         return "\n\n".join(context)
#     except Exception as e:
#         print(f"tools.compliance_retriever_tool failed :{e}")
#         raise
