# 🏥 SHIFA Knowledge Assistant

An Enterprise RAG (Retrieval-Augmented Generation) Knowledge Assistant for hospital documents. Hospital staff can ask natural-language questions about policies and procedures, and get grounded, cited answers — generated only from official documents, never invented.

> ⚠️ **DEMO / SYNTHETIC HOSPITAL DATA — NOT FOR REAL CLINICAL USE**
> This project uses a fictional hospital ("SHIFA General Hospital") and entirely synthetic documents created for demonstration and testing purposes. It is a knowledge/policy assistant, not a medical diagnosis system.

---

## What it does

- Answers staff questions across 16 hospital documents (Emergency, Admissions, Patient Safety, Pharmacy, Nursing, Billing & Finance)
- Retrieves the most relevant document chunks using semantic search (FAISS + sentence embeddings)
- Generates grounded answers using Groq LLM, strictly based on retrieved context
- Cites sources with filename, department, page number, and excerpt
- Refuses to answer when the information isn't in the documents, instead of guessing

## Architecture

**Build-time (run once, offline):**
