"""
retriever.py  (Phase 7)
Saved FAISS index aur chunks load karta hai, aur ek sawaal ke liye Top-K sabse
milte-julte chunks dhoondhta hai. Isi function ko Phase 8 (RAG pipeline) aur
Phase 10 (Streamlit app) dono use karenge.
"""

import pickle
from pathlib import Path

import faiss
import numpy as np

from embedder import embed_texts

KB_DIR = Path("knowledge_base")


def load_knowledge_base(kb_dir=KB_DIR):
    """Saved FAISS index aur chunks (text+metadata) load karta hai. Documents re-process NAHI hote."""
    kb_dir = Path(kb_dir)
    index = faiss.read_index(str(kb_dir / "faiss.index"))
    with open(kb_dir / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def retrieve(query, index, chunks, top_k=3, min_score=0.0):
    """
    Ek sawaal ke liye Top-K sabse milte-julte chunks dhoondhta hai.
    Har result mein chunk ka text, metadata, aur uska similarity score (0 to 1) hota hai.
    """
    query_vector = embed_texts([query], show_progress=False).astype("float32")
    scores, indices = index.search(query_vector, top_k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:                 # FAISS itne results na mile to -1 deta hai
            continue
        if score < min_score:
            continue
        chunk = dict(chunks[idx])
        chunk["score"] = float(score)
        results.append(chunk)

    return results


if __name__ == "__main__":
    index, chunks = load_knowledge_base()
    results = retrieve("What is the deposit for ICU admission?", index, chunks, top_k=3)
    for r in results:
        print(f"{r['score']:.3f} | {r['filename']} (p{r['page']}) | {r['text'][:100]}")
        
