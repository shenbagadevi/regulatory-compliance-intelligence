from src.core.config import (
    OPENAI_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VECTOR_SEARCH_K,
    KEYWORD_SEARCH_K,
    FINAL_SEARCH_K,
    DB_CONNECTION,
    DB_CONNECTION_FTS,
    COLLECTION_NAME,
    DATA_DIR,
)

print("\n===== Configuration Test =====")

print(f"OPENAI_MODEL      : {OPENAI_MODEL}")
print(f"DB_CONNECTION     : {DB_CONNECTION}")
print(f"DB_CONNECTION_FTS : {DB_CONNECTION_FTS}")
print(f"COLLECTION_NAME   : {COLLECTION_NAME}")
print(f"CHUNK_SIZE        : {CHUNK_SIZE}")
print(f"CHUNK_OVERLAP     : {CHUNK_OVERLAP}")
print(f"VECTOR_SEARCH_K   : {VECTOR_SEARCH_K}")
print(f"KEYWORD_SEARCH_K  : {KEYWORD_SEARCH_K}")
print(f"FINAL_SEARCH_K    : {FINAL_SEARCH_K}")
print(f"DATA_DIR          : {DATA_DIR}")

print("\nConfiguration loaded successfully.")

# uv run python -m tests.test_config
