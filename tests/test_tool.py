from src.tools.tools import compliance_retriever_tool

query = "What are RBI gold loan guidelines?"

result = compliance_retriever_tool.invoke({"query": query})

print(result)


# how to run test process

# uv run python -m tests.test_tool
