import faiss
import numpy as np
from app.rag.embeddings import embed

class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []

    def build(self, chunks):
        vectors = embed(chunks)
        vectors = np.array(vectors).astype("float32")

        self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)
        self.chunks = chunks

    def search(self, query, k=4):
        q_vec = embed([query])
        q_vec = np.array(q_vec).astype("float32")

        distances, indices = self.index.search(q_vec, k)
        return [self.chunks[i] for i in indices[0]]
