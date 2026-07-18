from tools.tools import compliance_retriever

query = "What are RBI gold loan guidelines?"

result = compliance_retriever.invoke({"query": query})

print(result)


# how to run test process

# uv run python -m tests.test_tool

