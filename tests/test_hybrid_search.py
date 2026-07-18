from tools.tools import hybrid_search

query = "RBI gold loan"

docs = hybrid_search(query=query, vector_k=5, keyword_k=5, final_k=5)

print(f"\nDocuments Found : {len(docs)}\n")

for i, doc in enumerate(docs, start=1):
    print("=" * 80)
    print(f"Document {i}")
    print("=" * 80)

    print("\nMetadata")
    print(doc.metadata)

    print("\nContent")
    print(doc.page_content[:500])
    print()


# how to run test process

# uv run python -m tests.test_hybrid_search
