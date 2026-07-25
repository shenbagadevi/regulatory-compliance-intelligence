"""
Stores retrieved documents for the current request.

Simple implementation for single-user/demo applications.
Can later be replaced with request-scoped storage or Redis.
"""

from langchain_core.documents import Document

_last_retrieved_documents: list[Document] = []


def set_documents(docs: list[Document]) -> None:
    global _last_retrieved_documents
    _last_retrieved_documents = docs


def get_documents() -> list[Document]:
    return _last_retrieved_documents


def clear_documents() -> None:
    global _last_retrieved_documents
    _last_retrieved_documents = []
