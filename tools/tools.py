from core.db import get_vector_store


def vector_search(query: str, k: int = 5):
    """
    Perform semantic similarity search.

    Args:
        query (str): User question
        k (int): Number of documents to retrieve

    Returns:
        List[Document]
    """

    vector_store = get_vector_store(pre_delete_collection=False)

    results = vector_store.similarity_search(query=query, k=k)

    print("vector search ended ")

    return results
