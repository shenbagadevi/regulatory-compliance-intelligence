from agents.rag_agent import ask_compliance_agent

question = "What are RBI Gold Loan Guidelines?"

answer = ask_compliance_agent(question)

print("\n==============================")
print("Final Answer")
print("==============================")
print(answer)
