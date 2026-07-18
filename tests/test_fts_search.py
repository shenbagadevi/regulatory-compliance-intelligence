from tools.tools import keyword_search

docs = keyword_search("gold loan")

print(f"Documents Found: {len(docs)}")

for doc in docs:
    print("-" * 50)
    print(doc.page_content[:200])
    print(doc.metadata)


# how to run test process

# uv run python -m tests.test_fts_search
