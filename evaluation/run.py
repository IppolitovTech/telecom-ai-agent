"""Evaluation layer (ROADMAP Stage 6).

Two independent checks:
1. Retrieval accuracy — for questions with a known `expected_source`, does
   `rag/retriever.retrieve()` return that document as the top-1 hit?
2. Out-of-domain fabrication check — for questions with `expected_source: null`,
   does the full agent (`agent/router.handle_chat`) avoid attaching a source
   instead of confidently citing one? Runs the real LLM, so `LLM_TEMPERATURE`
   is forced to 0 for deterministic results, and a failed API call for one
   question is reported and skipped rather than aborting the whole run.
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("LLM_TEMPERATURE", "0")

EVAL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVAL_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import logging  # noqa: E402

logging.basicConfig(level=logging.WARNING)
# agent.router already turns LLM failures into a valid ChatResponse(error=True)
# per the Stage 4 error contract — the traceback it logs is noise here, since
# check_no_fabrication reports degraded responses itself.
logging.getLogger("agent.router").setLevel(logging.CRITICAL)


def load_questions() -> list[dict]:
    return json.loads((EVAL_DIR / "questions.json").read_text(encoding="utf-8"))


def check_retrieval_accuracy(questions: list[dict]) -> None:
    from rag.retriever import retrieve

    positive = [q for q in questions if q["expected_source"] is not None]
    correct = 0

    print("Retrieval accuracy:")
    for item in positive:
        chunks = retrieve(item["question"], k=1)
        actual = chunks[0].document if chunks else None
        is_correct = actual == item["expected_source"]
        correct += is_correct
        print(f"  [{'OK' if is_correct else 'FAIL'}] {item['question']!r} -> expected={item['expected_source']!r} actual={actual!r}")

    accuracy = (correct / len(positive) * 100) if positive else 0.0
    print()
    print(f"Questions: {len(positive)}")
    print(f"Correct source retrieved: {correct}/{len(positive)}")
    print(f"Retrieval accuracy: {accuracy:.0f}%")


def check_no_fabrication(questions: list[dict]) -> None:
    negative = [q for q in questions if q["expected_source"] is None]
    if not negative:
        return

    from agent.router import handle_chat
    from models.chat import ChatRequest

    print()
    print("Out-of-domain fabrication check (full agent, temperature=0):")
    passed = 0
    skipped = 0
    for i, item in enumerate(negative):
        response = handle_chat(ChatRequest(message=item["question"], session_id=f"eval-negative-{i}"))

        if response.error:
            print(f"  [SKIP] {item['question']!r} -> agent returned a degraded response (LLM call failed)")
            skipped += 1
            continue

        ok = not response.sources
        passed += ok
        print(f"  [{'OK' if ok else 'FAIL'}] {item['question']!r} -> sources={response.sources}")

    checked = len(negative) - skipped
    print()
    print(f"No fabricated source: {passed}/{checked}" + (f" ({skipped} skipped)" if skipped else ""))


if __name__ == "__main__":
    all_questions = load_questions()
    check_retrieval_accuracy(all_questions)
    check_no_fabrication(all_questions)
