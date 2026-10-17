# 🏥 SHIFA Knowledge Assistant

An Enterprise RAG (Retrieval-Augmented Generation) Knowledge Assistant for hospital documents. Hospital staff can ask natural-language questions about policies and procedures, and get grounded, cited answers — generated only from official documents, never invented.

> ⚠️ **DEMO / SYNTHETIC HOSPITAL DATA — NOT FOR REAL CLINICAL USE**
> This project uses a fictional hospital ("SHIFA General Hospital") and entirely synthetic documents created for demonstration and testing purposes. It is a knowledge/policy assistant, not a medical diagnosis system.

---

## What it does

- Answers staff questions across 16 hospital documents (Emergency, Admissions, Patient Safety, Pharmacy, Nursing, Billing & Finance)
- Retrieves the most relevant document chunks using semantic search (FAISS + sentence embeddings)
- Generates grounded answers using Groq LLM, strictly based on retrieved context
- Streams answers into the chat interface as they are generated
- Supports English, Urdu, and Roman Urdu questions with multilingual retrieval
- Cites sources with filename, department, page number, and excerpt
- Refuses to answer when the information isn't in the documents, instead of guessing

## Architecture

**Build-time (run once, offline):**

```text
documents/ -> document_loader.py -> chunker.py -> embedder.py
																			|                 |
																			+----------> build_index.py
																												|
															knowledge_base/faiss.index + chunks.pkl

User question -> semantic retrieval + lexical grounding gate
							-> grounded Groq response -> parsed source citations
```

The Streamlit app loads the pre-built index and never re-processes documents at
runtime. Retrieval rejects low-similarity or lexically unsupported context before
the LLM call, and answers include citations such as `[S1]` that map to document,
department, page, and excerpt metadata.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build_index.py  # required after changing the embedding model or documents
export GROQ_API_KEY="gsk_..."
streamlit run app.py
```

For Streamlit Cloud, add `GROQ_API_KEY` under **Settings -> Secrets**. Never
commit the key. Local embeddings are downloaded once and cached by
`sentence-transformers`.

## Evaluation

Run the offline retrieval benchmark without using Groq:

```bash
python evaluate.py
```

It reports answerable-question document hit rate and retrieval-level refusal
accuracy from `evaluation_questions.csv`. The refusal metric checks whether
retrieval is empty; it is not a substitute for evaluating the generated answer.

## Limitations and future work

- Retrieval now uses a multilingual embedding model for Urdu and Roman Urdu;
	answers still depend on the language capability of the selected Groq model.
- Semantic retrieval can still find broadly related policy text for an
	out-of-scope question. A BM25 hybrid search and cross-encoder reranker would
	improve precision.
- The benchmark does not call the LLM, so citation correctness and generated
	answer quality need a separate API-backed evaluation run.
- The knowledge base is build-time only. An authenticated admin upload and
	re-index workflow would be appropriate for production use.
