from agents.tool import function_tool
from app.rag.vector_store import VectorStore

vector_store = VectorStore()


@function_tool
def retrieve_legislation_context(query: str) -> str:
    """
    Retrieves relevant legislative sections from vector store.
    """
    results = vector_store.search(query)
    return "\n\n".join(results)
