"""Scoped hybrid retrieval over the curated statutory corpus.

In the real system (ARCHITECTURE.md) this is pgvector + Postgres tsvector
against a few thousand chunks. For the proof of concept, against a ~15-chunk
curated corpus, we don't need real embeddings to prove the *architecture* —
so this implements a lightweight stand-in for both halves of the hybrid:

  - "keyword" half : exact term overlap (stand-in for tsvector full-text)
  - "vector" half   : bag-of-words cosine similarity (stand-in for pgvector)

The combination logic and the classification/jurisdiction scoping are real;
only the similarity math is simplified. Swapping in real embeddings later is
a drop-in replacement for `_vector_score`.
"""

import math
import re
from collections import Counter
from typing import Dict, List

from .models import StatutoryChunk

STOPWORDS = {
    "the", "a", "an", "of", "for", "to", "in", "and", "or", "is", "on",
    "with", "this", "that", "shall", "any", "be", "not", "which",
}


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _keyword_score(query_tokens: List[str], chunk_tokens: List[str]) -> float:
    if not query_tokens or not chunk_tokens:
        return 0.0
    overlap = len(set(query_tokens) & set(chunk_tokens))
    return overlap / len(set(query_tokens))


def _vector_score(query_tokens: List[str], chunk_tokens: List[str]) -> float:
    """Bag-of-words cosine similarity — a deliberately simple stand-in for
    real sentence embeddings, kept dependency-free for the prototype."""
    qc, cc = Counter(query_tokens), Counter(chunk_tokens)
    all_terms = set(qc) | set(cc)
    dot = sum(qc[t] * cc[t] for t in all_terms)
    qnorm = math.sqrt(sum(v * v for v in qc.values()))
    cnorm = math.sqrt(sum(v * v for v in cc.values()))
    if qnorm == 0 or cnorm == 0:
        return 0.0
    return dot / (qnorm * cnorm)


def retrieve(
    classification: str,
    query_text: str,
    corpus: List[Dict],
    top_k: int = 5,
) -> List[StatutoryChunk]:
    """Scoped hybrid retrieval: only chunks tagged for this classification
    are eligible at all (matches the real system's classification+jurisdiction
    scoping), then ranked by a 0.5/0.5 blend of keyword and vector score."""
    query_tokens = _tokenize(query_text)
    scored = []

    for raw in corpus:
        if classification not in raw["applies_to"]:
            continue
        chunk_tokens = _tokenize(raw["text"])
        k_score = _keyword_score(query_tokens, chunk_tokens)
        v_score = _vector_score(query_tokens, chunk_tokens)
        hybrid = 0.5 * k_score + 0.5 * v_score
        if hybrid <= 0:
            continue
        scored.append(
            StatutoryChunk(
                chunk_id=raw["chunk_id"],
                act=raw["act"],
                section=raw["section"],
                text=raw["text"],
                applies_to=raw["applies_to"],
                relevance_score=round(hybrid, 4),
            )
        )

    scored.sort(key=lambda c: c.relevance_score, reverse=True)
    return scored[:top_k]
