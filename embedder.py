"""
embedder.py  (Phase 5)
Chunk ke text ko embeddings (numbers ki list) mein badalta hai, sentence-transformers
ka multilingual model use karke. Ye wahi model hai jo build_index.py (Phase 6)
aur app.py (Phase 10) dono mein use hoga, taaki numbers compare-able rahein.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None   # model ek baar load hoke cache mein reh jaata hai (bar bar load na ho)


def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME} (pehli baar thoda time lagega)...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts, batch_size=32, show_progress=True):
    """
    Texts ki list leta hai, embeddings (numbers ki list ki list) wapas deta hai.
    Example: embed_texts(["hello", "world"]) -> numpy array shape (2, 384)
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True,   # FAISS similarity search ke liye zaroori (Phase 6 mein)
    )
    return embeddings


def embed_chunks(chunks, batch_size=32):
    """Chunk-records ki list leta hai, har chunk ka 'text' embed karta hai."""
    texts = [c["text"] for c in chunks]
    return embed_texts(texts, batch_size=batch_size)


if __name__ == "__main__":
    sample = ["What is the triage process?", "ICU room charges per day"]
    vectors = embed_texts(sample)
    print("Shape:", vectors.shape)
