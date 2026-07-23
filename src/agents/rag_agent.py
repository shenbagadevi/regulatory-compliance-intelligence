from langchain.agents import create_agent
from src.tools.tools import (
    hybrid_retriever_tool,
    keyword_retriever_tool,
    semantic_retriever_tool,
)
from src.core.config import OPENAI_MODEL
from src.agents.prompt_template import SYS_PROMPT
from src.schemas.compliance_response import ComplianceResponse
import os

rag_agent = create_agent(
    model=OPENAI_MODEL,
    tools=[
        semantic_retriever_tool,
        keyword_retriever_tool,
        hybrid_retriever_tool,
    ],
    system_prompt=SYS_PROMPT,
    response_format=ComplianceResponse,
)


def ask_compliance_agent(question: str) -> ComplianceResponse:
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
            },
        },
    )

    return response["structured_response"]
