from __future__ import annotations

import faiss
import numpy as np
from pathlib import Path
from typing import List

from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

from app.config import LLM_MODEL, get_llm_openai_client

# ==============================
# Configuration
# ==============================
REPO_ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = REPO_ROOT / "data" / "sample_legislation.pdf"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
FAISS_INDEX_PATH = REPO_ROOT / "data" / "faiss.index"
CHUNKS_PATH = REPO_ROOT / "data" / "chunks.txt"

client = get_llm_openai_client()

# ==============================
# Load Embedding Model
# ==============================

embedding_model = SentenceTransformer(EMBED_MODEL_NAME)

# ==============================
# PDF Loader
# ==============================

def load_pdf_text(pdf_path: str | Path) -> List[str]:
    reader = PdfReader(str(pdf_path))
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return pages


# ==============================
# Chunking
# ==============================

def chunk_text(text_list: List[str], chunk_size: int = 500) -> List[str]:
    chunks = []

    for text in text_list:
        words = text.split()
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

    return chunks


# ==============================
# Build FAISS Index (Run Once)
# ==============================

def build_vector_store():
    print("Building FAISS index...")

    pages = load_pdf_text(PDF_PATH)
    chunks = chunk_text(pages)

    embeddings = embedding_model.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, str(FAISS_INDEX_PATH))

    # Save chunks for retrieval
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.replace("\n", " ") + "\n\n")

    print("FAISS index built successfully.")


# ==============================
# Load Vector Store
# ==============================

def load_vector_store():
    if not FAISS_INDEX_PATH.exists():
        build_vector_store()

    index = faiss.read_index(str(FAISS_INDEX_PATH))

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = f.read().split("\n\n")

    return index, chunks


# ==============================
# Query RAG
# ==============================

def query_rag(query: str, top_k: int = 3) -> str:
    index, chunks = load_vector_store()

    query_embedding = embedding_model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    retrieved_context = "\n\n".join([chunks[i] for i in indices[0]])

    prompt = f"""
You are a legal compliance assistant.

Use the provided context to answer the question.

Context:
{retrieved_context}

Question:
{query}

Answer clearly and professionally.
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a financial compliance expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()
