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


def ask_compliance_agent(question: str) -> ComplianceResponseLLM:
    """
    Invoke the Compliance RAG Agent.
    """

    try:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        logger.info("Compliance query received.")
        logger.debug("Question: %s", question)

        response = rag_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ]
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

        structured_response = response.get("structured_response")

        if structured_response is None:
            logger.error("structured_response not found in agent response.")
            raise RuntimeError("Invalid response returned by Compliance Agent.")

        logger.info("Compliance query processed successfully.")

        return structured_response

    except ValueError:
        logger.exception("Validation error while processing compliance query.")
        raise

    except KeyError:
        logger.exception("Missing expected key in agent response.")
        raise

    except Exception:
        logger.exception("Unexpected error while invoking Compliance Agent.")
        raise
