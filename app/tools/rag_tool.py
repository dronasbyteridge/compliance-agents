from app.rag.vector_store import VectorStore

vector_store = VectorStore()

def initialize_vector_store(chunks):
    vector_store.build(chunks)

def rag_tool(query: str) -> str:
    results = vector_store.search(query)
    return "\n\n".join(results)
