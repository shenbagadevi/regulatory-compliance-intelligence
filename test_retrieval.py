from tools.tools import vector_search

results = vector_search("What are the KYC requirements?")

print("=" * 80)
print(f"Number of documents retrieved: {len(results)}")


for i, doc in enumerate(results, start=1):
    print(f"\nResult {i}")
    print("-" * 80)
    print(doc.page_content)

    print("\nMetadata:")
    print(doc.metadata)

    print("=" * 80)


# how to run retrieval process

# uv run python test_retrieval.py
