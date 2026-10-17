"""
rag_pipeline.py  (Phase 8 + Phase 9)
Retrieved chunks ko context mein badalta hai, strict grounding instruction ke saath
Groq LLM ko bhejta hai, jawaab wapas deta hai, aur sirf un sources ki structured
citation list banata hai jo LLM ne asal mein apne jawaab mein use kiye.
"""

import os
import re
from groq import Groq

from retriever import load_knowledge_base, retrieve

GROQ_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are SHIFA Knowledge Assistant, a policy and procedure assistant for hospital staff at SHIFA General Hospital.

STRICT RULES:
1. Answer only from the provided hospital document context below. Do not use any outside knowledge.
2. If sufficient information is not available in the context, clearly say that the answer could not be found in the available documents. Do not guess or make up an answer.
3. When you use information from a source, refer to it using its tag, like [S1] or [S2]. Cite every factual claim.
4. This is a knowledge/policy assistant, not a medical diagnosis system. Do not give clinical advice beyond what is written in the policies.
5. Be concise and direct. Use short paragraphs or bullet points where helpful.
6. Answer in the same language as the staff question. If the question is in Urdu, answer in Urdu script. If it is in Roman Urdu, answer in clear Roman Urdu. Keep source tags such as [S1] unchanged.
"""


def get_groq_client(api_key=None):
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY nahi mili. Isse environment variable ya argument se pass karo.")
    return Groq(api_key=api_key)


def build_context(chunks):
    """
    Retrieved chunks ko numbered source blocks mein badalta hai, jaise:
    [S1] Source: EM-01_Emergency_Admission_Policy.pdf (Emergency, page 1)
    <chunk text>

    Har chunk ko uska tag ("S1", "S2"...) bhi assign karke wapas deta hai, taaki
    baad mein extract_cited_sources() isi mapping se match kar sake.
    """
    blocks = []
    tagged_chunks = []
    for i, chunk in enumerate(chunks, start=1):
        tag = f"S{i}"
        header = f"[{tag}] Source: {chunk['filename']} ({chunk['department']}, page {chunk['page']})"
        blocks.append(f"{header}\n{chunk['text']}")
        chunk_with_tag = dict(chunk)
        chunk_with_tag["tag"] = tag
        tagged_chunks.append(chunk_with_tag)
    return "\n\n---\n\n".join(blocks), tagged_chunks


def extract_cited_sources(answer_text, tagged_chunks, excerpt_len=200):
    """
    Answer text mein se [S1], [S2] jaise tags dhoondhta hai, aur sirf unhi
    chunks ki structured citation list banata hai jo asal mein use hue.
    Agar LLM ne koi tag use hi nahi kiya (ya "not found" jawaab diya), khaali list aati hai.
    """
    citation_groups = re.findall(r"\[S(\d+(?:\s*,\s*S?\d+)*)\]", answer_text, flags=re.IGNORECASE)
    used_tags = {
        number
        for group in citation_groups
        for number in re.findall(r"\d+", group)
    }

    cited = []
    for chunk in tagged_chunks:
        tag_number = chunk["tag"].lstrip("S")
        if tag_number in used_tags:
            cited.append({
                "tag": chunk["tag"],
                "filename": chunk["filename"],
                "title": chunk["title"],
                "department": chunk["department"],
                "page": chunk["page"],
                "score": round(chunk["score"], 3),
                "excerpt": chunk["text"][:excerpt_len].strip() + ("..." if len(chunk["text"]) > excerpt_len else ""),
            })

    # Tag number ke hisaab se sort karo (S1, S2, S3...) taaki order saaf rahe
    cited.sort(key=lambda c: int(c["tag"].lstrip("S")))
    return cited


def answer_question(question, index, chunks_db, client, top_k=4, temperature=0.1):
    """
    Poora RAG flow: question -> retrieve -> Groq -> grounded answer -> cited sources.

    Return karta hai:
    {
        "answer": str,                 # LLM ka jawaab, [S1] tags ke saath
        "cited_sources": list,         # sirf wo sources jo jawaab mein use hue
        "all_retrieved": list,         # debugging ke liye, sab retrieved chunks
    }
    """
    retrieved = retrieve(question, index, chunks_db, top_k=top_k)

    if not retrieved:
        return {
            "answer": "The answer could not be found in the available documents.",
            "cited_sources": [],
            "all_retrieved": [],
        }

    # 2. Context banao (tags ke saath)
    context_text, tagged_chunks = build_context(retrieved)

    # 3. Groq ko prompt bhejo
    user_message = f"""Context from hospital documents:

{context_text}

---

Staff question: {question}

Answer the question using only the context above. Cite sources using their tags like [S1], [S2]."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=600,
    )

    answer_text = response.choices[0].message.content

    # 4. Sirf cited sources nikaalo
    cited_sources = extract_cited_sources(answer_text, tagged_chunks)

    return {
        "answer": answer_text,
        "cited_sources": cited_sources,
        "all_retrieved": tagged_chunks,
    }


def stream_answer(question, index, chunks_db, client, top_k=4, temperature=0.1):
    """Return a text generator and mutable state for a streaming RAG response."""
    state = {"cited_sources": [], "all_retrieved": []}

    def generate():
        retrieved = retrieve(question, index, chunks_db, top_k=top_k)
        if not retrieved:
            answer_text = "The answer could not be found in the available documents."
            state["answer"] = answer_text
            yield answer_text
            return

        context_text, tagged_chunks = build_context(retrieved)
        state["all_retrieved"] = tagged_chunks
        user_message = f"""Context from hospital documents:

{context_text}

---

Staff question: {question}

Answer the question using only the context above. Answer in the same language as the question. Cite sources using their tags like [S1], [S2]."""

        response_stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=600,
            stream=True,
        )

        parts = []
        for event in response_stream:
            content = event.choices[0].delta.content
            if content:
                parts.append(content)
                yield content

        answer_text = "".join(parts)
        state["answer"] = answer_text
        state["cited_sources"] = extract_cited_sources(answer_text, tagged_chunks)

    return generate(), state


def format_sources_display(cited_sources):
    """Citation list ko ek readable text block mein format karta hai (Streamlit se pehle quick-check ke liye)."""
    if not cited_sources:
        return "(No sources cited)"

    lines = []
    for s in cited_sources:
        lines.append(f"[{s['tag']}] {s['filename']} | {s['department']} | Page {s['page']} | score={s['score']}")
        lines.append(f"    \"{s['excerpt']}\"")
    return "\n".join(lines)


if __name__ == "__main__":
    index, chunks_db = load_knowledge_base()
    client = get_groq_client()
    result = answer_question("What is the deposit for ICU admission?", index, chunks_db, client)
    print(result["answer"])
    print("\nSources:")
    print(format_sources_display(result["cited_sources"]))
