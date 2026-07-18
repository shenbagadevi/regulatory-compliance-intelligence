from agents.rag_agent import ask_compliance_agent


def query_service(question: str) -> str:
    """
    Processes a user question using the Compliance RAG Agent.
    """

    try:
        answer = ask_compliance_agent(question)
        return answer
    except Exception as e:
        print(f"services.query_service failed :{e}")
        raise
