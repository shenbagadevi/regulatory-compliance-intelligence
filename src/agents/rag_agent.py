from langchain.agents import create_agent
from src.tools.tools import (
    hybrid_retriever_tool,
    keyword_retriever_tool,
    semantic_retriever_tool,
)
from src.schemas.retrieval_store import get_documents

from src.core.config import OPENAI_MODEL
from src.agents.prompt_template import SYS_PROMPT
from src.schemas.compliance_response import ComplianceResponseLLM, AgentResponse


def get_last_retrieved_documents():
    return get_documents()


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


def ask_compliance_agent(question: str) -> ComplianceResponseLLM:
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
    # tool_messages = response["messages"]
    return response["structured_response"]
    # source_documents=source_documents,
    # )
