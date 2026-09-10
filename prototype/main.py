#!/usr/bin/env python3
"""
IP-SAKTI proof-of-concept CLI.

Runs the real pipeline logic (classify -> retrieve -> synthesize -> verify ->
score -> escalate) against a small curated statutory corpus. No database, no
auth, no frontend — this exists to prove the verification-gate architecture
described in WHITEPAPER.md and ARCHITECTURE.md, not to be a deployable app.

Usage:
    python main.py                          # run built-in demo scenarios
    python main.py --formulation my.json     # run one formulation from a file
    python main.py --demo bad-citation       # force a citation failure to
                                              # show the verifier catching it
    python main.py --use-llm                 # use a real LLM for synthesis
                                              # (requires ANTHROPIC_API_KEY)
"""

import argparse
import json
import os
import sys

from ip_sakti import classifier, retrieval, synthesis, citation_verifier

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_RETRIES = 2

DEMO_SCENARIOS = {
    "classical": {
        "ingredients": ["ashwagandha", "milk"],
        "extraction_method": "traditional decoction, sun-dried powder",
        "intended_use": "general wellness and stress support",
        "claims_text": "Rejuvenating tonic prepared following traditional method.",
        "jurisdiction": "IN",
    },
    "phytopharma": {
        "ingredients": ["ashwagandha root"],
        "extraction_method": "standardized extract, purified fraction, 98% withanolide content",
        "intended_use": "clinical anxiety management",
        "claims_text": "A standardized extract with defined bioactive compounds for a specific therapeutic use.",
        "jurisdiction": "IN",
    },
    "aahar": {
        "ingredients": ["turmeric", "black pepper", "ginger"],
        "extraction_method": "dried and powdered, blended",
        "intended_use": "daily health drink / functional food supplement",
        "claims_text": "A dietary nutraceutical supplement for general immunity.",
        "jurisdiction": "IN",
    },
    "patent_proprietary": {
        "ingredients": ["neem", "synthetic carrier compound"],
        "extraction_method": "novel proprietary process, chemically modified extraction",
        "intended_use": "targeted antimicrobial treatment",
        "claims_text": "A novel synthesized formulation with a proprietary process not found in classical texts.",
        "jurisdiction": "IN",
    },
    "ambiguous": {
        "ingredients": ["unlisted proprietary blend"],
        "extraction_method": "undisclosed method",
        "intended_use": "general purpose",
        "claims_text": "A blend intended for multiple undefined uses.",
        "jurisdiction": "IN",
    },
}


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def run_pipeline(formulation: dict, corpus: list, classical_texts: list,
                  use_llm: bool = False, force_bad_citation: bool = False) -> dict:
    print("\n" + "=" * 70)
    print("STAGE 1 — Deterministic Classification (no LLM)")
    print("=" * 70)
    result = classifier.classify(formulation, classical_texts)
    classification = result["classification"]
    for line in result["trace"]:
        print(f"  · {line}")
    print(f"  → Classification: {classification}")
    if result["tkrc_match"]:
        m = result["tkrc_match"]
        print(f"  → TKRC directional match: {m['tkrc_code']} ({m['name']}, {m['source_text']})")

    query_text = " ".join([
        " ".join(formulation.get("ingredients", [])),
        formulation.get("extraction_method", ""),
        formulation.get("claims_text", ""),
    ])

    print("\n" + "=" * 70)
    print("STAGE 2 — Scoped Hybrid Retrieval (keyword + vector-like)")
    print("=" * 70)
    chunks = retrieval.retrieve(classification, query_text, corpus, top_k=5)
    if chunks:
        for c in chunks:
            print(f"  · [{c.relevance_score:.3f}] {c.act} {c.section} (chunk_id={c.chunk_id})")
    else:
        print("  · No relevant chunks retrieved for this classification/query.")

    steps = None
    failed_claims = []
    retries_used = 0
    inject_this_attempt = force_bad_citation

    while retries_used <= MAX_RETRIES:
        label = "STAGE 3 — LLM Synthesis" if retries_used == 0 else f"STAGE 3 — Retry {retries_used}"
        print("\n" + "=" * 70)
        print(label)
        print("=" * 70)
        steps = synthesis.synthesize(
            formulation, classification, chunks,
            use_llm=use_llm, inject_bad_citation=inject_this_attempt,
        )
        for s in steps:
            cites = ", ".join(f"{c.act} {c.section}" for c in s.citations) or "(no citations)"
            print(f"  · [{s.risk_level.upper()}] {s.action}")
            print(f"      cites: {cites}")

        print("\n" + "-" * 70)
        print("STAGE 4 — Citation Verifier (hard gate)")
        print("-" * 70)
        passed, failed_claims = citation_verifier.verify(steps, chunks)
        if passed:
            print("  ✓ All citations verified against retrieved chunks.")
            break
        else:
            for f in failed_claims:
                print(f"  ✗ {f}")
            retries_used += 1
            inject_this_attempt = False  # only the first draft is corrupted for the demo
            if retries_used <= MAX_RETRIES:
                print(f"  → Verification failed. Retrying synthesis ({retries_used}/{MAX_RETRIES})...")
            else:
                print("  → Max retries exhausted. Routing to escalation.")

    print("\n" + "=" * 70)
    print("STAGE 5 — Confidence Scoring & Escalation Routing")
    print("=" * 70)
    confidence = citation_verifier.confidence_score(steps, failed_claims, chunks, classification)
    escalate, reason = citation_verifier.should_escalate(confidence, classification)
    if retries_used > MAX_RETRIES:
        escalate, reason = True, "system_citation_failure"

    print(f"  confidence_score = {confidence}")
    if escalate:
        print(f"  → ESCALATED (reason: {reason}) — not shown to user unverified / unresolved.")
    else:
        print("  → DELIVERED — verified roadmap ready for the user.")

    return {
        "classification": classification,
        "tkrc_match": result["tkrc_match"],
        "chunks_retrieved": len(chunks),
        "steps": steps,
        "confidence_score": confidence,
        "status": "escalated" if escalate else "delivered",
        "escalation_reason": reason if escalate else None,
        "retries_used": retries_used,
    }


def main():
    parser = argparse.ArgumentParser(description="IP-SAKTI proof-of-concept pipeline")
    parser.add_argument("--formulation", help="Path to a formulation JSON file")
    parser.add_argument(
        "--demo", choices=list(DEMO_SCENARIOS.keys()) + ["all", "bad-citation"],
        default="all", help="Which built-in demo scenario to run",
    )
    parser.add_argument("--use-llm", action="store_true",
                         help="Use a real LLM for synthesis (requires ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    corpus = load_json(os.path.join(HERE, "data", "corpus.json"))
    classical_texts = load_json(os.path.join(HERE, "data", "classical_texts.json"))

    if args.formulation:
        formulation = load_json(args.formulation)
        run_pipeline(formulation, corpus, classical_texts, use_llm=args.use_llm)
        return

    if args.demo == "bad-citation":
        print("\n### DEMO: forcing a hallucinated citation to show the verifier catch it ###")
        run_pipeline(
            DEMO_SCENARIOS["patent_proprietary"], corpus, classical_texts,
            use_llm=args.use_llm, force_bad_citation=True,
        )
        return

    scenarios = DEMO_SCENARIOS if args.demo == "all" else {args.demo: DEMO_SCENARIOS[args.demo]}
    for name, formulation in scenarios.items():
        print(f"\n\n########## SCENARIO: {name} ##########")
        run_pipeline(formulation, corpus, classical_texts, use_llm=args.use_llm)


if __name__ == "__main__":
    sys.exit(main())
