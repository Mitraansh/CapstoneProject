"""
RAG knowledge-base search for qualitative activity questions.

Uses keyword matching against activity descriptions when no FAISS index
is available (trainer-recommended fallback for capstone demos).
"""

from pathlib import Path
import re


def _load_kb_chunks() -> list[tuple[str, float]]:
    """Load knowledge chunks from activity data and optional KB markdown files."""
    chunks: list[tuple[str, float]] = []

    try:
        from src.app import activities

        for name, data in activities.items():
            text = (
                f"{name}: {data['description']}. "
                f"Schedule: {data['schedule']}. "
                f"Max participants: {data['max_participants']}."
            )
            chunks.append((text, 1.0))
    except ImportError:
        pass

    kb_dir = Path(__file__).parent.parent.parent / "vector-store"
    if kb_dir.is_dir():
        for md_file in kb_dir.glob("*.md"):
            chunks.append((md_file.read_text(encoding="utf-8"), 0.9))

    return chunks


def _score_chunk(question: str, chunk: str) -> float:
    """Simple keyword overlap score between question and chunk."""
    question_words = set(re.findall(r"[a-z0-9]+", question.lower()))
    chunk_words = set(re.findall(r"[a-z0-9]+", chunk.lower()))
    if not question_words:
        return 0.0
    overlap = len(question_words & chunk_words)
    return overlap / len(question_words)


def rag_search(question: str) -> dict:
    """
    Search the knowledge base for an answer to a qualitative question.

    Returns dict with answer, source, and confidence keys.
    """
    chunks = _load_kb_chunks()
    if not chunks:
        return {
            "answer": "I couldn't find information about that in our knowledge base.",
            "source": "rag",
            "confidence": 0.0,
        }

    scored = [(chunk, _score_chunk(question, chunk)) for chunk, _ in chunks]
    scored.sort(key=lambda item: item[1], reverse=True)
    top_chunk, top_score = scored[0]

    if top_score < 0.5:
        return {
            "answer": "I couldn't find information about that in our knowledge base.",
            "source": "rag",
            "confidence": 0.0,
        }

    return {
        "answer": top_chunk,
        "source": "rag",
        "confidence": min(top_score, 1.0),
    }
