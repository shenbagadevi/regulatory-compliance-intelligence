from src.agents.rag_agent import ask_compliance_agent
from src.schemas.compliance_response import ComplianceResponse, Citation
import logging, shutil, uuid


def query_service(question: str) -> str:
    """
    Processes a user question using the Compliance RAG Agent.
    """

    try:
        answer = ask_compliance_agent(question)
        # return answer
        print("query service retruning data")
        return ComplianceResponse(
            query=question,
            answer=answer,
            citations=[
                Citation(
                    document="N/A",
                    section="N/A",
                    page=1,
                )
            ],
            rule_summary=["No compliance rules available."],
            confidence_score=0.0,
            disclaimer=(
                "This response is generated from a placeholder "
                "implementation. Verify regulatory information "
                "before making compliance decisions."
            ),
            langsmith_trace_id=str(uuid.uuid4()),
        )

    except Exception as e:
        print(f"services.query_service failed :{e}")
        raise
