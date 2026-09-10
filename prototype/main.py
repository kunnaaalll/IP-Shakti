#!/usr/bin/env python3
"""
IP-SAKTI proof-of-concept CLI.

Runs the complete pipeline logic (classify -> retrieve -> synthesize -> verify ->
score -> escalate) against a curated statutory corpus, displaying the complete
strategic analytical dossier in the terminal:
  · Stage 1: Deterministic Classification & TKRC Prior Art Match
  · Stage 2: Scoped Hybrid Statutory Retrieval
  · Stage 3: Strategic Roadmap Synthesis
  · Stage 4: Citation Verifier Gate with Hallucination Intercept & Self-Healing
  · Stage 5: Confidence Scoring & Escalation Routing
  · Comprehensive Strategic IP Roadmap Dossier (by Phase, Risk, Authority, Deliverable)
  · 5-Axis Sovereign Risk & Posture Radar Profile (Visual Bar Chart)
  · AYUSH Geographical Indications (GI) Strategic Registry & Terroir Intelligence
  · Mandatory NBA Form 3 Sovereign Compliance Protocol

Usage:
    python main.py                          # run default scenario
    python main.py --demo all               # run all 5 built-in scenarios
    python main.py --demo classical         # run specific scenario
    python main.py --demo bad-citation       # show the gatekeeper catch a hallucination
    python main.py --formulation my.json     # run from custom formulation JSON
    python main.py --json                   # emit pure structured JSON
    python main.py --brief                  # emit high-level executive summary
    python main.py --export report.md       # export complete dossier to file
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from ip_sakti import classifier, retrieval, synthesis, citation_verifier
from ip_sakti.gi_registry import get_radar_metrics, get_gi_strategy, GI_HUBS, SCENARIO_GI_MAP

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_RETRIES = 2


def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[error] File not found: {path}", file=sys.stderr)
        return {} if "scenario" in path else []
    except json.JSONDecodeError as exc:
        print(f"[error] Invalid JSON in {path}: {exc}", file=sys.stderr)
        return {} if "scenario" in path else []


DEMO_SCENARIOS = load_json(os.path.join(HERE, "data", "scenarios.json"))


def format_bar(val: float, width: int = 20) -> str:
    """Renders a fixed-width visual bar chart for terminal output."""
    filled = int(round(val * width))
    empty = width - filled
    return "[" + "#" * filled + "." * empty + "]"


def render_banner():
    print("=" * 80)
    print("  IP-SAKTI : AYURVEDA IP SOVEREIGNTY NAVIGATOR (CLI ENGINE)")
    print("  Statutory Verification Gatekeeper | BDA 2002 | Patents Act 1970 | GI Act 1999")
    print("=" * 80)


def print_intercept_box(failed_claim: str):
    print("  +" + "-" * 76 + "+")
    print("  | [!] GATEKEEPER INTERCEPTED FABRICATED CITATION (PASS 1)" + " " * 19 + "|")
    print("  +" + "-" * 76 + "+")
    print("  | * Verification Rule : Hard Grounding Gate (Act + Section + Chunk ID)" + " " * 7 + "|")
    print(f"  | * Citation Fault    : {failed_claim[:68]:<68} |")
    if len(failed_claim) > 68:
        print(f"  |                       {failed_claim[68:136]:<68} |")
    print("  | * Gatekeeper Action : Rejecting synthesis draft & triggering" + " " * 15 + "|")
    print("  |                       automated self-healing loop (Attempt 1 of 2)..." + " " * 8 + "|")
    print("  +" + "-" * 76 + "+")


def print_healed_box():
    print("  +" + "-" * 76 + "+")
    print("  | [*] SELF-HEALING REPAIR SUCCESSFUL (PASS 2)" + " " * 31 + "|")
    print("  +" + "-" * 76 + "+")
    print("  | * All statutory citations verified against retrieved corpus chunks      |")
    print("  | * Status: Gatekeeper Cleared -- zero hallucinated legal provisions       |")
    print("  +" + "-" * 76 + "+")


def run_pipeline(formulation: dict, corpus: list, classical_texts: list,
                 use_llm: bool = False, force_bad_citation: bool = False,
                 brief: bool = False, quiet: bool = False) -> dict:
    """Executes the 5-stage sovereign pipeline and outputs the full analytical dossier."""
    def p(*args, **kwargs):
        if not quiet:
            print(*args, **kwargs)

    if not quiet:
        render_banner()

    form_name = formulation.get("name") or "Unnamed Ayurvedic Formulation"
    ingredients = formulation.get("ingredients") or []
    method = formulation.get("extraction_method") or "Standard Extraction"
    claims = formulation.get("claims_text") or "Not Specified"
    jurisdiction = formulation.get("jurisdiction") or "IN"

    p(f"\n[FORMULATION DOSSIER]")
    p(f"  Name        : {form_name}")
    p(f"  Ingredients : {', '.join(ingredients)}")
    p(f"  Extraction  : {method}")
    p(f"  Claims      : {claims}")
    p(f"  Jurisdiction: {jurisdiction}")

    # STAGE 1: Classification
    p("\n" + "=" * 80)
    p("STAGE 1 — Deterministic Classification (No LLM)")
    p("=" * 80)
    result = classifier.classify(formulation, classical_texts)
    classification = result["classification"]
    for line in result["trace"]:
        p(f"  · {line}")
    p(f"  → Result Classification: [{classification.upper()}]")
    if result.get("tkrc_match"):
        m = result["tkrc_match"]
        p(f"  → TKRC Directional Prior Art Match: {m['tkrc_code']}")
        p(f"      Botanical / Treatise : {m.get('name', 'N/A')}")
        p(f"      Classical Text       : {m.get('source_text', 'N/A')}")
        p(f"      Subgroup Code        : {m.get('subgroup', 'A61K 36/00')}")

    # STAGE 2: Retrieval
    query_text = " ".join([
        " ".join(ingredients),
        str(method),
        str(claims),
    ])
    p("\n" + "=" * 80)
    p("STAGE 2 — Scoped Hybrid Retrieval (Keyword + Vector Density)")
    p("=" * 80)
    chunks = retrieval.retrieve(classification, query_text, corpus, top_k=8)
    if chunks:
        p(f"  Retrieved {len(chunks)} scoped statutory chunks:")
        for c in chunks:
            p(f"  · [{c.relevance_score:.3f}] {c.act} {c.section} (chunk_id={c.chunk_id})")
    else:
        p("  · No relevant statutory chunks retrieved.")

    # STAGE 3 & 4: Synthesis & Verification Loop
    steps = None
    failed_claims = []
    retries_used = 0
    inject_this_attempt = force_bad_citation

    while retries_used <= MAX_RETRIES:
        label = "STAGE 3 — Roadmap Synthesis" if retries_used == 0 else f"STAGE 3 — Synthesis Retry {retries_used}"
        p("\n" + "=" * 80)
        p(label)
        p("=" * 80)
        steps = synthesis.synthesize(
            formulation, classification, chunks,
            use_llm=use_llm, inject_bad_citation=inject_this_attempt,
        )
        p(f"  Synthesized draft containing {len(steps)} actionable roadmap steps.")

        p("\n" + "-" * 80)
        p("STAGE 4 — Citation Verifier (Hard Gatekeeper)")
        p("-" * 80)
        passed, failed_claims = citation_verifier.verify(steps, chunks)
        if passed:
            if retries_used > 0:
                if not quiet:
                    print_healed_box()
            else:
                p("  ✓ All citations strictly ground-truth verified against retrieved chunks.")
            break
        else:
            for f in failed_claims:
                if not quiet:
                    print_intercept_box(f)
            retries_used += 1
            inject_this_attempt = False  # only corrupt first attempt
            if retries_used <= MAX_RETRIES:
                p(f"  → Retrying synthesis with grounded prompt ({retries_used}/{MAX_RETRIES})...")
            else:
                p("  → Max retries exhausted. Routing to escalation.")

    # STAGE 5: Confidence & Escalation
    p("\n" + "=" * 80)
    p("STAGE 5 — Confidence Scoring & Escalation Routing")
    p("=" * 80)
    confidence = citation_verifier.confidence_score(steps, failed_claims, chunks, classification)
    escalate, reason = citation_verifier.should_escalate(confidence, classification)
    if retries_used > MAX_RETRIES:
        escalate, reason = True, "system_citation_failure"

    p(f"  Confidence Score : {confidence:.3f} / 1.000 ({confidence * 100:.1f}%)")
    if escalate:
        p(f"  Routing Decision : [ESCALATED]")
        p(f"  Escalation Cause : {reason}")
        p(f"  Protocol Action  : Blocked from unverified execution. Routed to Human IP Cell.")
    else:
        p(f"  Routing Decision : [DELIVERED — ROADMAP VERIFIED]")
        p(f"  Protocol Action  : Approved for strategic commercial & patent execution.")

    # 5-AXIS RADAR RISK METRICS
    radar_metrics = get_radar_metrics(classification)
    p("\n" + "=" * 80)
    p("SOVEREIGN RISK & POSTURE RADAR PROFILE (5-Axis Vector)")
    p("=" * 80)
    for m in radar_metrics:
        bar = format_bar(m["val"], width=20)
        pct = int(round(m["val"] * 100))
        p(f"  · {m['label']:<34} {bar} {pct:>3}%  {m.get('desc', '')}")
    p("-" * 80)
    p(f"  Composite Sovereign IP Index : {confidence * 100:.1f}%")

    # AYUSH GEOGRAPHICAL INDICATIONS (GI) REGISTRY
    gi_info = get_gi_strategy(classification)
    strat = gi_info["strategy"]
    hub = gi_info["hub"]

    p("\n" + "=" * 80)
    p("AYUSH GEOGRAPHICAL INDICATIONS (GI) STRATEGIC REGISTRY")
    p("=" * 80)
    p(f"  Strategic Focus  : {strat.get('badge', 'GI STRATEGIC DEFENSE')}")
    p(f"  Strategic Lead   : {strat.get('lead', '')}")
    p(f"  Legal Analysis   : {strat.get('text', '')}\n")
    p(f"  Recommended Hub  : {hub.get('title', '')}")
    p(f"  State / Region   : {hub.get('state', '')}")
    p(f"  Statutory Reg.   : {hub.get('reg_no', '')} | {hub.get('statute', '')}")
    p(f"  Certified Items  :")
    for item in hub.get("items", []):
        p(f"    - {item}")
    p(f"  Phytochemicals   : {hub.get('phytochem_marker', 'HPLC Validated')}")
    p(f"  Classical Source : {hub.get('treatise_ref', 'Ayurvedic Pharmacopoeia of India')}")
    p(f"  Export Premium   : {hub.get('export_premium', '+45% to +75%')}")
    p(f"  FPO Collective   : {hub.get('fpo_association', 'State Herb Collective')}")

    # COMPREHENSIVE ROADMAP DOSSIER
    if not brief and steps:
        p("\n" + "=" * 80)
        p(f"COMPREHENSIVE STRATEGIC IP ROADMAP DOSSIER ({len(steps)} STEPS)")
        p("=" * 80)

        nba_triggered = False
        for idx, s in enumerate(steps, start=1):
            risk_tag = f"[{s.risk_level.upper()}]"
            phase_tag = s.phase or f"Phase {idx}"
            p(f"\n[STEP {idx}] {phase_tag}")
            p(f"  Action               : {s.action}")
            p(f"  Risk Level           : {risk_tag}")
            if s.governing_authority:
                p(f"  Governing Authority  : {s.governing_authority}")
            if s.statutory_hazard:
                p(f"  Statutory Hazard     : {s.statutory_hazard}")
            if s.deliverable:
                p(f"  Actionable Deliver   : {s.deliverable}")
            if s.operational_guidance:
                p(f"  Operational Guidance : {s.operational_guidance}")
            cites_str = ", ".join(f"{c.act} {c.section} (chunk_id={c.chunk_id})" for c in s.citations) or "(no citations)"
            p(f"  Statutory Citations  : {cites_str}")
            if s.timeline_note:
                p(f"  Timeline Horizon     : {s.timeline_note}")
            if s.rationale:
                p(f"  Strategic Rationale  : {s.rationale}")

            # Check if NBA compliance is triggered
            for c in s.citations:
                if "Biological Diversity" in c.act or "NBA" in str(s.governing_authority):
                    nba_triggered = True

        if nba_triggered:
            p("\n" + "=" * 80)
            p("MANDATORY NBA FORM 3 SOVEREIGN COMPLIANCE PROTOCOL")
            p("=" * 80)
            p("  Statutory Mandate : Section 6 of the Biological Diversity Act, 2002 requires mandatory")
            p("                      prior approval from the National Biodiversity Authority (NBA)")
            p("                      before applying for any Intellectual Property right in or outside India.")
            p("  Criminal Hazard   : Section 55 imposes imprisonment up to 5 years and/or fine up to Rs. 10 Lakhs.")
            p("  Filing Authority  : National Biodiversity Authority, TICEL Bio Park, Taramani, Chennai.")
            p("  Sovereign Action  : Execute SBB commercial intimation (Section 7) and complete Form 3")
            p("                      with proven origin documentation prior to IPO patent examination.")

    p("\n" + "=" * 80)
    p("END OF IP-SAKTI STATUTORY DOSSIER")
    p("=" * 80 + "\n")

    return {
        "formulation": formulation,
        "classification": classification,
        "tkrc_match": result.get("tkrc_match"),
        "chunks_retrieved": len(chunks),
        "steps": [
            {
                "step": s.step,
                "action": s.action,
                "phase": s.phase,
                "risk_level": s.risk_level,
                "governing_authority": s.governing_authority,
                "statutory_hazard": s.statutory_hazard,
                "deliverable": s.deliverable,
                "operational_guidance": s.operational_guidance,
                "timeline_note": s.timeline_note,
                "rationale": s.rationale,
                "citations": [{"act": c.act, "section": c.section, "chunk_id": c.chunk_id} for c in s.citations],
            }
            for s in steps
        ] if steps else [],
        "confidence_score": confidence,
        "status": "escalated" if escalate else "delivered",
        "escalation_reason": reason if escalate else None,
        "retries_used": retries_used,
        "radar_metrics": radar_metrics,
        "gi_strategy": gi_info,
    }


def main():
    parser = argparse.ArgumentParser(
        description="IP-SAKTI: Ayurveda IP Sovereignty Strategic Engine (CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--formulation", help="Path to a formulation JSON file")
    parser.add_argument(
        "--demo", choices=list(DEMO_SCENARIOS.keys()) + ["all", "bad-citation"],
        default="classical", help="Which built-in demo scenario to run (default: classical)",
    )
    parser.add_argument("--use-llm", action="store_true",
                        help="Use a real LLM for synthesis (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--json", action="store_true",
                        help="Emit pure structured JSON output")
    parser.add_argument("--brief", action="store_true",
                        help="Output concise executive summary without full step breakdowns")
    parser.add_argument("--export", metavar="PATH",
                        help="Export the output report to a file")
    args = parser.parse_args()

    corpus = load_json(os.path.join(HERE, "data", "corpus.json"))
    classical_texts = load_json(os.path.join(HERE, "data", "classical_texts.json"))

    quiet = bool(args.json)
    results = []

    if args.formulation:
        formulation = load_json(args.formulation)
        res = run_pipeline(formulation, corpus, classical_texts, use_llm=args.use_llm,
                           brief=args.brief, quiet=quiet)
        results.append(res)
    elif args.demo == "bad-citation":
        res = run_pipeline(
            DEMO_SCENARIOS["patent_proprietary"], corpus, classical_texts,
            use_llm=args.use_llm, force_bad_citation=True, brief=args.brief, quiet=quiet,
        )
        results.append(res)
    elif args.demo == "all":
        for name, formulation in DEMO_SCENARIOS.items():
            res = run_pipeline(formulation, corpus, classical_texts, use_llm=args.use_llm,
                               brief=args.brief, quiet=quiet)
            results.append(res)
    else:
        formulation = DEMO_SCENARIOS.get(args.demo, DEMO_SCENARIOS["classical"])
        res = run_pipeline(formulation, corpus, classical_texts, use_llm=args.use_llm,
                           brief=args.brief, quiet=quiet)
        results.append(res)

    if args.json:
        payload = results if len(results) > 1 else results[0]
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            payload = results if len(results) > 1 else results[0]
            if args.export.endswith(".json"):
                json.dump(payload, f, indent=2, ensure_ascii=False)
            else:
                f.write(f"# IP-SAKTI Strategic IP Dossier Export\n\n")
                f.write("```json\n")
                f.write(json.dumps(payload, indent=2, ensure_ascii=False))
                f.write("\n```\n")
        if not quiet:
            print(f"[success] Report successfully exported to {args.export}")


if __name__ == "__main__":
    sys.exit(main())
