"""Offline retrieval evaluation using evaluation_questions.csv.

This script deliberately does not call Groq. It measures whether the expected
document is retrieved and whether out-of-scope questions are rejected before
generation.
"""

import argparse
import csv
from pathlib import Path

from retriever import load_knowledge_base, retrieve


def load_questions(path):
    with Path(path).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def evaluate(questions, index, chunks, top_k):
    answerable = [row for row in questions if row["answer_available"].lower() == "yes"]
    refusals = [row for row in questions if row["answer_available"].lower() != "yes"]

    hits = 0
    for row in answerable:
        results = retrieve(row["question"], index, chunks, top_k=top_k)
        expected = row["expected_document"]
        if any(result["filename"] == expected for result in results):
            hits += 1

    rejected = 0
    for row in refusals:
        if not retrieve(row["question"], index, chunks, top_k=top_k):
            rejected += 1

    return {
        "total": len(questions),
        "answerable": len(answerable),
        "retrieval_hits": hits,
        "retrieval_hit_rate": hits / len(answerable) if answerable else 0.0,
        "refusal_questions": len(refusals),
        "refusal_correct": rejected,
        "refusal_accuracy": rejected / len(refusals) if refusals else 0.0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="evaluation_questions.csv")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    index, chunks = load_knowledge_base()
    metrics = evaluate(load_questions(args.questions), index, chunks, args.top_k)
    print(f"Retrieval hit rate: {metrics['retrieval_hits']}/{metrics['answerable']} "
          f"({metrics['retrieval_hit_rate']:.1%})")
    print(f"Refusal accuracy: {metrics['refusal_correct']}/{metrics['refusal_questions']} "
          f"({metrics['refusal_accuracy']:.1%})")


if __name__ == "__main__":
    main()