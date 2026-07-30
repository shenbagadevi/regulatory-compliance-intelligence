import logging

# Import only to initialize logging configuration
from src.core import logger

from langchain.agents import create_agent

from src.tools.tools import (
    hybrid_retriever_tool,
    keyword_retriever_tool,
    semantic_retriever_tool,
)
from src.schemas.retrieval_store import get_documents
from src.core.config import OPENAI_MODEL
from src.agents.prompt_template import SYS_PROMPT
from src.schemas.compliance_response import ComplianceResponseLLM

# Module logger
logger = logging.getLogger(__name__)


def get_last_retrieved_documents():
    """
    Returns the last retrieved documents.
    """
    try:
        documents = get_documents()

        if documents is None:
            logger.warning("No retrieved documents found.")
            return []

        return documents

    except Exception:
        logger.exception("Failed to retrieve last retrieved documents.")
        raise


# Initialize RAG Agent
try:
    rag_agent = create_agent(
        model=OPENAI_MODEL,
        tools=[
            semantic_retriever_tool,
            keyword_retriever_tool,
            hybrid_retriever_tool,
        ],
        system_prompt=SYS_PROMPT,
        response_format=ComplianceResponseLLM,
    )

    logger.info("Compliance RAG Agent initialized successfully.")

except Exception:
    logger.exception("Failed to initialize Compliance RAG Agent.")
    raise

chat_history = []


def ask_compliance_agent(question: str) -> ComplianceResponseLLM:
    messages = chat_history.copy()

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    response = rag_agent.invoke(
        {
            "messages": messages,
        },
        config={
            "run_name": "ComplianceAgent",
            "tags": [
                "rag",
                "compliance",
                "retrieval",
            ],
            "metadata": {
                "application": "RegulatoryComplianceSystem",
                "version": "1.0",
                "query": question,
                "query_length": len(question),
            },
        },
    )

    structured_response = response["structured_response"]

    # Save only the latest conversation
    chat_history.append(
        {
            "role": "user",
            "content": question,
        }
    )

    chat_history.append(
        {
            "role": "assistant",
            "content": structured_response.answer,
        }
    )

    # Keep only the last 10 messages (5 user/assistant exchanges)
    if len(chat_history) > 10:
        del chat_history[:-10]

    return structured_response
