# retrieval_context.py

from dataclasses import dataclass
from langchain_core.documents import Document


@dataclass
class RetrievalContext:
    docs: list[Document]
    confidence: float
    tool_used: str
