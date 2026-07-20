from langchain.agents import create_agent
from src.tools.tools import compliance_retriever_tool
from src.core.config import OPENAI_MODEL
import os

rag_agent = create_agent(
    model=OPENAI_MODEL,
    tools=[compliance_retriever_tool],
    system_prompt="""
You are an expert Regulatory Compliance Assistant.

You MUST use the compliance_retriever_tool for every user question before generating an answer.

Answer ONLY using the information returned by the tool.

Do not rely on your own knowledge.

If the answer is not available in the retrieved documents, respond exactly:

'I couldn't find this information in the provided documents.'

Do not invent or assume facts.
""",
)


def ask_compliance_agent(question: str) -> str:
    response = rag_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        }
    )

    return response["messages"][-1].content
