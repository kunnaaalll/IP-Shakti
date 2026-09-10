"""The trust boundary: verifies every roadmap claim before it's allowed to
reach the user. This is a hard gate, not an advisory check — see
ARCHITECTURE.md 'Citation protocol'.
"""

import re
from typing import List, Tuple

from .models import RoadmapStep, StatutoryChunk

LEGAL_ASSERTION_MARKERS = [
    r"\bunder section\b", r"\bpursuant to\b", r"\bas per rule\b",
    r"\bbarred by\b", r"\brequired under\b", r"\bprohibited under\b",
]


def verify(
    steps: List[RoadmapStep], retrieved_chunks: List[StatutoryChunk]
) -> Tuple[bool, List[str]]:
    """Returns (passed, failed_claims). A step fails if any of its citations
    don't match a retrieved chunk's exact (act, section, chunk_id) triple, OR if its
    action/rationale text contains a legal-assertion marker with zero
    citations attached at all.
    """
    retrieved_triples = {
        (c.act.strip().lower(), c.section.strip().lower(), c.chunk_id.strip())
        for c in retrieved_chunks
    }
    failed = []

    for step in steps:
        for citation in step.citations:
            cit_triple = (
                citation.act.strip().lower(),
                citation.section.strip().lower(),
                citation.chunk_id.strip(),
            )
            if cit_triple not in retrieved_triples:
                failed.append(
                    f"Step {step.step}: cited {citation.act} {citation.section} "
                    f"(chunk_id={citation.chunk_id}) — not present in the retrieved chunk set."
                )

        combined_text = f"{step.action} {step.rationale}".lower()
        has_marker = any(re.search(m, combined_text) for m in LEGAL_ASSERTION_MARKERS)
        if has_marker and not step.citations:
            failed.append(
                f"Step {step.step}: contains a legal-assertion phrase but has zero citations attached."
            )

    return (len(failed) == 0, failed)


def citation_pass_rate(steps: List[RoadmapStep], failed_claims: List[str]) -> float:
    if not steps:
        return 0.0
    failed_step_numbers = set()
    for f in failed_claims:
        m = re.match(r"^Step\s+(\d+):", f)
        if m:
            failed_step_numbers.add(int(m.group(1)))
    passed = len(steps) - len(failed_step_numbers)
    return max(passed, 0) / len(steps)


def avg_retrieval_relevance(retrieved_chunks: List[StatutoryChunk]) -> float:
    if not retrieved_chunks:
        return 0.0
    return sum(c.relevance_score for c in retrieved_chunks) / len(retrieved_chunks)


def classification_certainty(classification: str) -> float:
    return 0.0 if classification == "Ambiguous" else 1.0


def confidence_score(
    steps: List[RoadmapStep],
    failed_claims: List[str],
    retrieved_chunks: List[StatutoryChunk],
    classification: str,
) -> float:
    """confidence = 0.5*citation_pass_rate + 0.3*avg_retrieval_relevance + 0.2*classification_certainty
    — formula and weights as specified in ARCHITECTURE.md."""
    cpr = citation_pass_rate(steps, failed_claims)
    arr = avg_retrieval_relevance(retrieved_chunks)
    cc = classification_certainty(classification)
    return round(0.5 * cpr + 0.3 * arr + 0.2 * cc, 4)


def should_escalate(confidence: float, classification: str) -> Tuple[bool, str]:
    if classification == "Ambiguous":
        return True, "ambiguous_classification"
    if confidence < 0.5:
        return True, "low_confidence"
    return False, ""
