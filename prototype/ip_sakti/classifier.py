"""Deterministic classification decision tree.

This is the one module in the whole pipeline the LLM never touches. Per
ARCHITECTURE.md invariant #2: classification must be deterministic given the
same inputs. Pure function, zero I/O, fully unit-testable in isolation.
"""

from typing import Dict, List

NOVEL_PROCESS_MARKERS = [
    "novel", "synthesized", "synthesised", "modified", "nano",
    "proprietary process", "new molecule", "chemically altered",
]

PHYTOPHARMA_MARKERS = [
    "standardized extract", "standardised extract", "purified fraction",
    "phytopharmaceutical", "bioactive fraction", "defined compounds",
    "98%", "standardized fraction", "standardised fraction",
]

AAHAR_MARKERS = [
    "food", "supplement", "nutraceutical", "dietary", "health drink",
    "functional food", "snack",
]


def _text_blob(formulation: Dict) -> str:
    parts = [
        formulation.get("extraction_method", ""),
        formulation.get("intended_use", ""),
        formulation.get("claims_text", ""),
    ]
    return " ".join(parts).lower()


def _matches_classical(formulation: Dict, classical_texts: List[Dict]) -> Dict:
    """Returns the matching classical-text entry, or None."""
    ingredients = [i.lower() for i in formulation.get("ingredients", [])]
    blob = _text_blob(formulation)

    # A formulation is only "Classical" if its core ingredients match a known
    # classical text AND the processing/claims described are traditional — no
    # novel-processing, standardized-fraction, or food/supplement framing.
    # A classical ingredient run through a standardized extraction process is
    # Phytopharmaceutical, not Classical; framed as a snack or supplement, it's
    # Aahar, not Classical. Ingredient overlap alone isn't enough.
    if any(marker in blob for marker in NOVEL_PROCESS_MARKERS + PHYTOPHARMA_MARKERS + AAHAR_MARKERS):
        return None

    for entry in classical_texts:
        core = [c.lower() for c in entry["core_ingredients"]]
        if any(c in " ".join(ingredients) for c in core):
            return entry
    return None


def classify(formulation: Dict, classical_texts: List[Dict]) -> Dict:
    """
    Returns {"classification": str, "tkrc_match": dict|None, "trace": [str]}

    The `trace` list is the explainability output recommended in the
    whitepaper — it's the actual decision path taken, not a post-hoc excuse,
    so it's cheap to surface to the user.
    """
    trace = []
    blob = _text_blob(formulation)

    classical_match = _matches_classical(formulation, classical_texts)
    if classical_match:
        trace.append(
            f"Core ingredient matches a documented classical formulation "
            f"('{classical_match['name']}', {classical_match['source_text']})."
        )
        trace.append("No novel-processing or standardized-fraction language detected.")
        return {"classification": "Classical", "tkrc_match": classical_match, "trace": trace}

    if any(marker in blob for marker in PHYTOPHARMA_MARKERS):
        trace.append("Extraction/claims language matches standardized-fraction criteria.")
        trace.append("Classified per AYUSH Phytopharmaceutical Drugs Notification, 2015 definition.")
        return {"classification": "Phytopharmaceutical", "tkrc_match": None, "trace": trace}

    if any(marker in blob for marker in AAHAR_MARKERS):
        trace.append("Intended use / claims frame this as food, supplement, or nutraceutical.")
        trace.append("Routed to FSSAI-governed classification (Aahar), not drug pathway.")
        return {"classification": "Aahar", "tkrc_match": None, "trace": trace}

    if any(marker in blob for marker in NOVEL_PROCESS_MARKERS):
        trace.append("Novel-processing language detected — not matched to a classical formulation.")
        trace.append("Routed to Patent & Proprietary pathway for novelty assessment.")
        return {"classification": "Patent&Proprietary", "tkrc_match": None, "trace": trace}

    trace.append("No clean match to Classical, Phytopharmaceutical, Aahar, or novel-process markers.")
    trace.append("Decision tree could not confidently place this formulation in one bucket.")
    return {"classification": "Ambiguous", "tkrc_match": None, "trace": trace}
