#!/usr/bin/env python3
"""
IP-SAKTI web server.

Wraps the existing pipeline modules in a Flask API with Server-Sent Events
so the frontend can animate each pipeline stage in real time.

Usage:
    pip install flask
    python app.py
    # then open http://localhost:5000
"""

import json
import os
import time

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from ip_sakti import citation_verifier, classifier, retrieval, synthesis

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_RETRIES = 1  # one retry, then escalate

app = Flask(__name__, static_folder="static", template_folder="templates")


def _load_json(filename):
    path = os.path.join(HERE, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[warning] Failed loading {path}: {exc}")
        return {} if "scenario" in filename else []


CORPUS = _load_json(os.path.join("data", "corpus.json"))
CLASSICAL_TEXTS = _load_json(os.path.join("data", "classical_texts.json"))
DEMO_SCENARIOS = _load_json(os.path.join("data", "scenarios.json"))


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def run_pipeline_sse(formulation: dict, force_bad_citation: bool = False):
    """Generator that yields SSE events for each pipeline stage."""
    try:
        # STAGE 1: Classification
        yield _sse("stage_start", {"stage": 1, "label": "Deterministic Classification"})
        time.sleep(0.4)

        result = classifier.classify(formulation, CLASSICAL_TEXTS)
        classification = result["classification"]

        yield _sse("stage_done", {
            "stage": 1,
            "classification": classification,
            "trace": result["trace"],
            "tkrc_match": result["tkrc_match"],
        })
        time.sleep(0.3)

        # STAGE 2: Retrieval
        yield _sse("stage_start", {"stage": 2, "label": "Scoped Hybrid Retrieval"})
        time.sleep(0.5)

        query_text = " ".join([
            " ".join(formulation.get("ingredients") or []),
            str(formulation.get("extraction_method") or ""),
            str(formulation.get("claims_text") or ""),
        ])
        chunks = retrieval.retrieve(classification, query_text, CORPUS, top_k=8)

        yield _sse("stage_done", {
            "stage": 2,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "act": c.act,
                    "section": c.section,
                    "relevance_score": c.relevance_score,
                    "text": c.text,
                }
                for c in chunks
            ],
        })
        time.sleep(0.3)

        # STAGE 3 + 4: Synthesis + Verification loop
        steps = None
        failed_claims = []
        retries_used = 0
        inject_this_attempt = force_bad_citation

        while retries_used <= MAX_RETRIES:
            label = "Roadmap Synthesis" if retries_used == 0 else f"Synthesis Retry {retries_used}"
            yield _sse("stage_start", {"stage": 3, "label": label, "attempt": retries_used})
            time.sleep(0.6)

            steps = synthesis.synthesize(
                formulation, classification, chunks,
                use_llm=False, inject_bad_citation=inject_this_attempt,
            )

            yield _sse("stage_done", {
                "stage": 3,
                "steps": [
                    {
                        "step": s.step,
                        "action": s.action,
                        "rationale": s.rationale,
                        "risk_level": s.risk_level,
                        "timeline_note": s.timeline_note,
                        "phase": s.phase,
                        "deliverable": s.deliverable,
                        "statutory_hazard": s.statutory_hazard,
                        "governing_authority": s.governing_authority,
                        "operational_guidance": s.operational_guidance,
                        "citations": [
                            {"act": c.act, "section": c.section, "chunk_id": c.chunk_id}
                            for c in s.citations
                        ],
                    }
                    for s in steps
                ],
                "attempt": retries_used,
            })
            time.sleep(0.4)

            # STAGE 4: Citation Verification
            yield _sse("stage_start", {"stage": 4, "label": "Citation Verifier Gate"})
            time.sleep(0.6)

            passed, failed_claims = citation_verifier.verify(steps, chunks)

            yield _sse("stage_done", {
                "stage": 4,
                "passed": passed,
                "failed_claims": failed_claims,
                "attempt": retries_used,
            })
            time.sleep(0.3)

            if passed:
                break

            retries_used += 1
            inject_this_attempt = False
            if retries_used > MAX_RETRIES:
                break

        # STAGE 5: Confidence + Escalation
        yield _sse("stage_start", {"stage": 5, "label": "Confidence Scoring & Escalation"})
        time.sleep(0.5)

        confidence = citation_verifier.confidence_score(steps, failed_claims, chunks, classification)
        escalate, reason = citation_verifier.should_escalate(confidence, classification)
        if retries_used > MAX_RETRIES:
            escalate, reason = True, "system_citation_failure"

        yield _sse("stage_done", {
            "stage": 5,
            "confidence_score": confidence,
            "escalate": escalate,
            "escalation_reason": reason if escalate else None,
            "status": "escalated" if escalate else "delivered",
            "retries_used": retries_used,
        })

        # Final complete event
        yield _sse("complete", {
            "classification": classification,
            "tkrc_match": result["tkrc_match"],
            "confidence_score": confidence,
            "status": "escalated" if escalate else "delivered",
            "escalation_reason": reason if escalate else None,
            "retries_used": retries_used,
            "steps": [
                {
                    "step": s.step,
                    "action": s.action,
                    "rationale": s.rationale,
                    "risk_level": s.risk_level,
                    "timeline_note": s.timeline_note,
                    "phase": s.phase,
                    "deliverable": s.deliverable,
                    "statutory_hazard": s.statutory_hazard,
                    "governing_authority": s.governing_authority,
                    "operational_guidance": s.operational_guidance,
                    "citations": [
                        {"act": c.act, "section": c.section, "chunk_id": c.chunk_id}
                        for c in s.citations
                    ],
                }
                for s in (steps or [])
            ],
        })
    except Exception as exc:
        yield _sse("pipeline_error", {"message": f"Pipeline execution error: {str(exc)}"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scenarios")
def scenarios():
    return jsonify(DEMO_SCENARIOS)


@app.route("/api/analyze", methods=["GET", "POST"])
def analyze():
    """SSE endpoint. Accepts formulation fields via GET query params or POST JSON."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "formulation" in data and isinstance(data["formulation"], dict):
            force_bad = bool(data.get("force_bad_citation", data["formulation"].get("force_bad_citation", False)))
            data = data["formulation"]
        else:
            force_bad = bool(data.get("force_bad_citation", False))
        raw_ing = data.get("ingredients", [])
        if isinstance(raw_ing, str):
            ingredients = [i.strip() for i in raw_ing.split(",") if i.strip()]
        elif isinstance(raw_ing, list):
            ingredients = [str(i).strip() for i in raw_ing if str(i).strip()]
        else:
            ingredients = []
        formulation = {
            "ingredients": ingredients,
            "extraction_method": data.get("extraction_method") or "",
            "intended_use": data.get("intended_use") or "",
            "claims_text": data.get("claims_text") or "",
            "jurisdiction": data.get("jurisdiction") or "IN",
        }
    else:
        ingredients_raw = request.args.get("ingredients", "")
        formulation = {
            "ingredients": [i.strip() for i in ingredients_raw.split(",") if i.strip()],
            "extraction_method": request.args.get("extraction_method") or "",
            "intended_use": request.args.get("intended_use") or "",
            "claims_text": request.args.get("claims_text") or "",
            "jurisdiction": request.args.get("jurisdiction") or "IN",
        }
        force_bad = request.args.get("force_bad_citation", "false").lower() == "true"

    def generate():
        yield from run_pipeline_sse(formulation, force_bad_citation=force_bad)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
