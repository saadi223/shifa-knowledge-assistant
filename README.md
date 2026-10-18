# 🏥 Shifa Hospital Assistant

**An AI assistant that answers hospital staff questions using the hospital's own policy documents, shows where each answer came from, and says "I don't know" instead of guessing.**

> ⚠️ **DEMO PROJECT, NOT FOR REAL MEDICAL USE.**
> "SHIFA General Hospital" is a fictional hospital. All 16 documents in this project are made-up (synthetic) and were created only for learning and testing. This is a policy and procedure helper. It is **not** a medical diagnosis tool.

*(Inside the app, the project appears under the name "SHIFA Knowledge Assistant".)*

---

## ⭐ Special feature: it understands Urdu and Roman Urdu

Most hospital staff do not always think or type in English. Shifa Hospital Assistant is built so that staff can ask in the language they are comfortable with:

| If the question is in... | Example | The assistant answers in... |
|---|---|---|
| **English** | *What is the deposit for ICU admission?* | English |
| **Urdu** (Urdu script) | آئی سی یو میں داخلے کا طریقہ کار کیا ہے؟ | Urdu |
| **Roman Urdu** (Urdu/Hindi in English letters) | *ICU mein admission ka process kya hai?* | Roman Urdu |

How this works, in simple words:

- The search model is **multilingual**, so a question in Urdu can match an English document by *meaning*, not by exact words.
- The AI is instructed to **reply in the same language as the question** and to keep the source tags like `[S1]` unchanged.
- The documents stay in English. Only the question and the answer change language.

The same safety rules apply in every language: answers come only from the documents, sources are shown, and if the answer is missing the assistant refuses.

*Please test your own questions in each language. See the [limitations](#13-limitations-honest-list) for known weak spots.*

---

## Table of contents

0. [⭐ Special feature: Urdu and Roman Urdu](#-special-feature-it-understands-urdu-and-roman-urdu)
1. [The problem this project solves](#1-the-problem-this-project-solves)
2. [What it can do](#2-what-it-can-do)
3. [See it in action](#3-see-it-in-action)
4. [How it works, step by step](#4-how-it-works-step-by-step)
5. [How it avoids wrong answers](#5-how-it-avoids-wrong-answers)
6. [The 16 documents it knows](#6-the-16-documents-it-knows)
7. [Technology used](#7-technology-used)
8. [What is inside the project](#8-what-is-inside-the-project)
9. [Run it on your own computer](#9-run-it-on-your-own-computer)
10. [Put it online (Streamlit Cloud)](#10-put-it-online-streamlit-cloud)
11. [Adding or changing documents](#11-adding-or-changing-documents)
12. [Testing the search quality](#12-testing-the-search-quality)
13. [Limitations (honest list)](#13-limitations-honest-list)
14. [Small dictionary](#14-small-dictionary)
15. [Disclaimer](#15-disclaimer)

---

## 1. The problem this project solves

A hospital has many rules written in many files: how to register a patient, what to do before giving a risky medicine, how much a room costs, when the pharmacy is open.

When a nurse, receptionist or billing officer needs one answer, opening and reading many PDF and Word files wastes time. And in a hospital, a *wrong* answer can be worse than no answer.

**Shifa Hospital Assistant** lets staff simply **ask a question in plain language** and get a short answer taken *only* from the official documents, together with the document name and page, so they can double-check it.

---

## 2. What it can do

| Feature | What it means |
|---|---|
| 💬 **Chat-style questions** | Type a normal question, like messaging a colleague. |
| 🌐 **Urdu, Roman Urdu and English** | Ask in English, in Urdu script, or in Roman Urdu (Urdu/Hindi written in English letters). The answer comes back in the same language. See [the special feature](#-special-feature-it-understands-urdu-and-roman-urdu). |
| 📚 **Sources shown** | Every answer lists the file name, department, page number and a short excerpt. |
| 🚫 **Honest refusals** | If the answer is not in the documents, it says so instead of inventing one. |
| ⚡ **Live typing** | The answer appears word by word while it is being written, so there is no long blank wait. |
| 🧪 **Built-in test** | A small script checks how well the search part works. |

---

## 3. See it in action

*(Examples are illustrative: they show the idea, not saved output.)*

**A question that is covered by the documents**

> **Staff:** How much is the daily charge and deposit for an ICU bed?
> **Assistant:** Gives the amounts from the "Room and Bed Charges" document.
> **Sources box:** `BF-04_Room_and_Bed_Charges.csv`, Billing & Finance, with a short excerpt.

**A question that is NOT covered**

> **Staff:** What is a staff nurse's monthly salary?
> **Assistant:** *"The answer could not be found in the available documents."*

The second case is on purpose. Salary is not in any document, so the assistant does not guess.

---

## 4. How it works, step by step

Imagine a **very fast librarian** who only answers from the books on the shelf.

**Part 1: Preparing the library (done once, before the app runs)**

1. **Read** all documents (PDF, Word, text, spreadsheet).
2. **Cut** them into small pieces, like index cards.
3. **Convert** each piece into a list of numbers that represents its *meaning*. Pieces about similar things get similar numbers. This is done by an "embedding model".
4. **Store** all the numbers in a fast search catalogue (called an *index*).

**Part 2: Answering a question (every time someone asks)**

5. The question is also converted to numbers.
6. The catalogue finds the pieces whose numbers are *closest*, meaning the most related ones.
7. A few safety checks run (see the next section).
8. The selected pieces go to an AI writer (a "large language model" running on a service called Groq) with a strict instruction: *"Answer only from these pieces. If the answer is not here, say so."*
9. The answer appears on screen, and each fact is tagged like `[S1]`, `[S2]`. These tags are matched to the document, department, page and excerpt shown in the **Sources** box.

```
 Documents ──► cut into pieces ──► turned into numbers ──► saved in an index
                                                               │ (done once)
 ──────────────────────────────────────────────────────────────┼────────────
                                                               ▼
 Staff question ──► find most related pieces ──► safety checks
                                                      │
                          ┌───────────────────────────┴──────────────┐
                          ▼                                          ▼
              Nothing good found                         Good pieces found
                          │                                          │
                          ▼                                          ▼
            "Not found in documents"          AI writes answer using ONLY them
                                              + sources shown below the answer
```

This approach is called **RAG** (Retrieval-Augmented Generation): first *retrieve* the right information, then *generate* an answer from it.

The app never re-reads the documents while running. It only loads the saved index, which makes it fast.

---

## 5. How it avoids wrong answers

Several layers protect against made-up answers:

1. **Similarity check:** if the best matching piece is not similar enough to the question, nothing is sent to the AI and the assistant refuses.
2. **Keyword check:** a matching piece must also share at least one meaningful word with the question.
3. **Strict instructions to the AI:** answer only from the given pieces, tag every fact with its source, never give medical diagnosis, and say "not found" when unsure.
4. **Sources always shown:** a human can quickly verify the answer.

No system is perfect, so staff should still check the sources for anything important.

---

## 6. The 16 documents it knows

All documents are synthetic. They are in the `documents/` folder in PDF, Word (`.docx`), text (`.txt`) and spreadsheet (`.csv`) formats.

| Department | Documents |
|---|---|
| **Admissions** | Patient Registration Procedure · Inpatient Admission and Discharge Procedure |
| **Billing & Finance** | Billing Policy · Accepted Payment Methods · Insurance and Refund Policy · Room and Bed Charges |
| **Emergency** | Emergency Admission Policy · Triage Guidelines |
| **Nursing** | Nursing Handover Procedure · Vital Signs Monitoring Policy |
| **Pharmacy** | Medication Dispensing Policy · High-Alert Medication Guidelines · Pharmacy Counter Timings |
| **Patient Safety** | Patient Identification Policy · Infection Prevention Guidelines · Fall Prevention Policy |

---

## 7. Technology used

| Tool | What it does, in simple words |
|---|---|
| **Python** | The programming language the project is written in |
| **Streamlit** | Creates the chat web page without needing web-design skills |
| **sentence-transformers** | Turns text into numbers that capture meaning (model: `paraphrase-multilingual-MiniLM-L12-v2`, which understands many languages) |
| **FAISS** | A very fast search catalogue for those numbers |
| **Groq** | The service that runs the AI that writes the final answer |
| **PyMuPDF, python-docx, pandas** | Read PDF, Word and CSV files |

Exact versions are listed in `requirements.txt`.

---

## 8. What is inside the project

| File / folder | What it is for |
|---|---|
| `app.py` | The chat screen that staff use |
| `document_loader.py` | Reads the documents |
| `chunker.py` | Cuts documents into small pieces |
| `embedder.py` | Turns pieces and questions into numbers |
| `build_index.py` | Builds the search index (run again whenever documents change) |
| `retriever.py` | Finds the best matching pieces and applies the safety checks |
| `rag_pipeline.py` | Connects everything: retrieval, the AI call, streaming, and source tags |
| `evaluate.py` | Test script for search quality |
| `evaluation_questions.csv` | Test questions with the expected document for each |
| `documents/` | The 16 hospital documents |
| `knowledge_base/` | The saved search index created by `build_index.py` |
| `hospital_documents.zip` | A zipped copy of the documents |
| `requirements.txt` | The list of tools to install |

---

## 9. Run it on your own computer

**What you need**

- Python 3 installed (a recent version, 3.11 or newer, is recommended)
- Git (or download the project as a ZIP from GitHub)
- A free account at [console.groq.com](https://console.groq.com) to create an **API key** (a secret password that lets the app use the AI)

**Step 1: Download the project**

```bash
git clone https://github.com/saadi223/shifa-knowledge-assistant
cd shifa-knowledge-assistant
```

**Step 2: Create a clean Python environment (recommended)**

```bash
python -m venv .venv
```
- Mac / Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

**Step 3: Install the required tools**

```bash
pip install -r requirements.txt
```

**Step 4: Build the search index**

```bash
python build_index.py
```
The first time, a language model is downloaded automatically, so this can take a few minutes and needs internet. You must run this step again whenever the documents or the embedding model change.

**Step 5: Give the app your Groq key**

Choose one way:

- *Environment variable* (Mac/Linux): `export GROQ_API_KEY="your-key-here"`
  (Windows PowerShell: `$env:GROQ_API_KEY="your-key-here"`)
- *Or* create a file `.streamlit/secrets.toml` containing:
  ```toml
  GROQ_API_KEY = "your-key-here"
  ```

🔐 **Never upload your key to GitHub.** Keep `secrets.toml` out of the repository.

**Step 6: Start the app**

```bash
streamlit run app.py
```
Your browser opens the chat page. Try one of the example questions in the sidebar.

---

## 10. Put it online (Streamlit Cloud)

1. Push the project to GitHub. Make sure the `knowledge_base/` folder (with `faiss.index`, `chunks.pkl`, `metadata.pkl`) is included, because the online app only loads the saved index.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **Create app**, choose this repository, branch `main`, and main file `app.py`.
4. Open **Advanced settings**, find **Secrets**, and add:
   ```toml
   GROQ_API_KEY = "your-key-here"
   ```
5. Click **Deploy**. The first start takes a while because tools and the language model must be installed and downloaded.

The free tier has limited memory, so the app may need extra care if it runs out of resources. If it sleeps after some time without visitors, the first answer after waking up can be slow.

---

## 11. Adding or changing documents

1. Put the new file (PDF, Word, text or CSV) in the `documents/` folder.
2. Run `python build_index.py` to rebuild the index.
3. Test the app locally.
4. Upload the updated `documents/` and `knowledge_base/` folders to GitHub.

If you change the embedding model, rebuilding the index is **mandatory**. An index made with a different model can give wrong results.

---

## 12. Testing the search quality

```bash
python evaluate.py
```

This runs the questions in `evaluation_questions.csv` and prints two numbers:

- **Retrieval hit rate:** for questions that *are* covered, how often the right document was found.
- **Refusal accuracy:** for questions that are *not* covered, how often the search correctly returned nothing.

It does **not** call the AI, so it is free and quick. It tests the *search* part only, not the quality of the written answers.

---

## 13. Limitations (honest list)

- **Only knows these 16 documents.** This is intentional, so it cannot use outside knowledge.
- **Roman Urdu and the keyword check:** the search model understands many languages, but the keyword safety check (section 5) only looks at English letters and English words. A question written fully in Roman Urdu, without any English word like "ICU" or "billing", may be refused even when the answer exists. Mixing in English words usually works better.
- **Urdu script and Hindi (Devanagari) script** have been tested less than English. Always try your own questions.
- **Answer language** depends on the AI model on Groq. It follows the instruction to reply in the question's language, but small mistakes in Urdu or Roman Urdu spelling are possible.
- **The similarity threshold** (how close a match must be) was chosen by hand and should be tuned using the test script.
- **Long pieces:** the embedding model reads only a limited length (about 128 tokens, which is roughly a short paragraph). Longer pieces may lose their ending when converted to numbers. Smaller pieces help.
- **Out-of-scope questions** about related topics can sometimes still find loosely related text. Combining keyword and meaning search with a "reranker" would improve this.
- **The AI can still make mistakes.** Always check the shown sources for important decisions.
- **Documents are loaded only at build time.** There is no upload screen yet, and a production system would need one with login and permissions.
- **Answer quality testing** (are the written answers and citations correct?) needs a separate test that uses the AI service.

---

## 14. Small dictionary

| Word | Meaning |
|---|---|
| **RAG** | Find the right information first, then let AI write the answer from it |
| **Chunk** | A small piece of a document |
| **Embedding** | A list of numbers that represents the *meaning* of a text |
| **Index (FAISS)** | A fast search catalogue of all embeddings |
| **LLM** | A large language model, the AI that writes text (here it runs on Groq) |
| **Grounded answer** | An answer based only on the provided documents |
| **Streaming** | Showing the answer word by word as it is written |
| **API key** | A secret password for using an online service |
| **Roman Urdu** | Urdu or Hindi written with English letters |

---

## 15. Disclaimer

This project uses fictional data for learning and demonstration. It is a policy and procedure assistant, not a medical diagnosis system, and must not be used to make decisions about real patients.
