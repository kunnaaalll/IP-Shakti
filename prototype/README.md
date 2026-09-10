# IP-SAKTI — Ayurveda IP Navigator

**Smart India Hackathon 2026 · Problem Statement SIH26045**

A decision-support system that takes an Ayurveda formulation description and returns
a **citation-verified IP strategy roadmap** — what's patentable, what's barred, what
approvals are needed, and what alternative protection routes exist.

Built on one non-negotiable principle: **no legal claim is ever shown to a user unless
it can be traced to a specific, retrieved section of law.**

---

## The Problem

India's AYUSH sector produces thousands of new formulations every year. But a first-time
formulator trying to understand their IP position faces a unique problem:

- A single formulation can simultaneously touch the **Patents Act, 1970** (§3(p) bars
  patents on traditional knowledge), the **Biological Diversity Act, 2002** (NBA approval
  before filing), the **Drugs & Cosmetics Act / FSSAI** (drug vs. food classification),
  and the **Geographical Indications Act** (alternative protection routes).
- The only reliable answer today requires a paid patent attorney who specialises in
  AYUSH IP — **scarce, expensive, and slow** for early-stage founders.
- The **TKDL** (the authoritative prior-art tool for this exact domain) is NDA-gated to
  patent offices by international agreement. No public tool can integrate it.

IP-SAKTI is the first-pass triage that compresses a multi-week, paid screening into a
minutes-long, free, citation-backed answer.

---

## Who It's For

| User | Job to be done |
|---|---|
| Individual AYUSH formulators / student innovators | First-pass IP triage before they can afford an attorney |
| Small AYUSH manufacturers | Screening multiple product ideas quickly |
| AYUSH incubators & Technology Business Incubators | Screening applicant portfolios at scale |
| Patent agents | A fast, citation-backed first draft of the classification |

Patent examiners and large pharma are explicitly **not** the target — they already have
TKDL access and in-house counsel.

---

## What the System Does

Given a formulation description (ingredients, extraction method, intended use, claims —
in English or Hindi), IP-SAKTI:

1. **Classifies** it deterministically into one of five buckets:
   `Classical | Patent&Proprietary | Phytopharmaceutical | Aahar | Ambiguous`
2. **Retrieves** the specific statutory sections relevant to that classification and jurisdiction
3. **Synthesises** a structured roadmap: what's barred, what's viable, what regulatory
   approvals are needed, and alternative routes (GI / Trademark / Design)
4. **Verifies** every claim in the roadmap against the statutory text actually retrieved —
   rejecting and regenerating anything that can't be proven
5. **Scores its own confidence** and routes low-confidence cases to a human reviewer
   instead of guessing
6. Returns `Ambiguous` when it genuinely can't classify — never forces an answer

---

## Why This Is Not "Just RAG"

A standard RAG pipeline retrieves text and asks an LLM to answer. It has no mechanism to
*prove* its output is correct. IP-SAKTI diverges at four structural points:

**a) Classification is LLM-free.**
The highest-stakes decision — which bucket a formulation falls into — is computed by a
deterministic decision tree, not inferred. A hallucination here would be most damaging;
so the LLM never touches it.

**b) Citations are a hard gate, not a courtesy.**
The model must emit citations as structured data `{act, section, chunk_id}`. A verifier
checks each against the chunk IDs actually retrieved. A secondary regex scan catches
paraphrased legal assertions with no citation attached. Any failure → retry → escalate.
The user never sees an unverified claim.

**c) "I don't know" is a designed output.**
`Ambiguous` is a valid terminal state with its own status and audit trail, not a failure.
Most RAG systems would hallucinate an answer from whatever was retrieved.

**d) Answers are versioned, not disposable.**
An Analysis is immutable once delivered. Law changes produce a new superseding Analysis.
A Freshness Monitor retroactively flags every prior analysis that relied on a
now-superseded section.

---

## Pipeline Architecture

```
Formulation Input (ingredients, method, claims, jurisdiction)
        │
        ▼
┌─────────────────────────────────┐
│  STAGE 1 — Deterministic        │  Pure logic, zero LLM, fully unit-testable.
│  Classification                 │  Output: Classical | Patent&Proprietary |
│                                 │  Phytopharmaceutical | Aahar | Ambiguous
└──────────────┬──────────────────┘
               │
        ▼
┌─────────────────────────────────┐
│  STAGE 2 — Scoped Hybrid        │  BM25 keyword + vector similarity,
│  Retrieval                      │  scoped to classification + jurisdiction.
│                                 │  Output: top-k StatutoryChunks
└──────────────┬──────────────────┘
               │
        ▼
┌─────────────────────────────────┐
│  STAGE 3 — Roadmap Synthesis    │  Rule-based (default) or real LLM call,
│                                 │  grounded strictly in retrieved chunks.
│                                 │  Output: RoadmapSteps with citations[]
└──────────────┬──────────────────┘
               │
        ▼
┌─────────────────────────────────┐
│  STAGE 4 — Citation Verifier    │  Hard gate. Tuple + chunk_id match.
│  Gate                           │  Regex scan for uncited legal assertions.
│                                 │  Fail → retry (max 1). Fail again → escalate.
└──────────────┬──────────────────┘
               │
        ▼
┌─────────────────────────────────┐
│  STAGE 5 — Confidence Scoring   │  confidence = 0.5×citation_pass_rate
│  & Escalation Routing           │            + 0.3×avg_retrieval_relevance
│                                 │            + 0.2×classification_certainty
│                                 │  < 0.5 → escalate. Ambiguous → always escalate.
└──────────────┬──────────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
 DELIVERED          ESCALATED
 (to user)      (to human reviewer)
```

---

## Confidence Formula

```
confidence = 0.5 × citation_pass_rate        (fraction of steps with verified citations)
           + 0.3 × avg_retrieval_relevance   (mean relevance score of retrieved chunks)
           + 0.2 × classification_certainty  (1.0 for clean terminal, 0.0 for Ambiguous)

Threshold: confidence < 0.5 → auto-escalate, even if citation verification passed.
```

---

## Classification Buckets

| Bucket | Trigger | Key Statute |
|---|---|---|
| **Classical** | Core ingredients match a documented classical formulation + no novel processing | Patents Act §3(p) — barred from standard patent |
| **Patent & Proprietary** | Novel process / synthetic carrier / chemically modified extraction | Patents Act §2(1)(j), §3(d) — novelty and efficacy bar |
| **Phytopharmaceutical** | Standardised extract / purified fraction / defined bioactive compounds | AYUSH Phytopharmaceutical Drugs Notification, 2015 |
| **Aahar** | Food, supplement, nutraceutical, health drink framing | Food Safety and Standards Act §22 (FSSAI pathway) |
| **Ambiguous** | No clean match to any bucket | Routes to human review — never forced |

---

## Project Structure

```
SIH/
├── README.md                        ← project overview
├── ARCHITECTURE.md                  ← full technical reference (data model, API, stack)
├── WHITEPAPER.md                    ← pitch document (problem, solution, impact)
├── .gitignore
└── prototype/
    ├── README.md                    ← this file
    ├── requirements.txt             ← optional deps (Flask + anthropic)
    ├── main.py                      ← CLI entry point
    ├── app.py                       ← web server entry point (Flask + SSE)
    ├── data/
    │   ├── corpus.json              ← ~15 hand-curated statutory chunks
    │   └── classical_texts.json    ← classical formulation / TKRC lookup table
    ├── ip_sakti/                    ← core pipeline package
    │   ├── __init__.py
    │   ├── models.py                ← dataclasses: StatutoryChunk, RoadmapStep, Citation
    │   ├── classifier.py            ← deterministic decision tree (no LLM)
    │   ├── retrieval.py             ← scoped hybrid retrieval (keyword + vector)
    │   ├── synthesis.py             ← rule-based + optional LLM roadmap drafting
    │   └── citation_verifier.py    ← hard gate + confidence formula + escalation
    └── templates/
        └── index.html               ← web UI (dark mode, live pipeline animation)
```

The `ip_sakti/` module layout mirrors the `domain/` boundaries in `ARCHITECTURE.md`
intentionally — moving to the full FastAPI service is a matter of adding persistence
and API routes around the same logic, not rewriting it.

---

## What's Real vs. Simulated in the Prototype

| Stage | Status |
|---|---|
| Classification | ✅ **Real** — deterministic decision tree, pure Python, zero LLM |
| Retrieval | ⚡ **Simplified** — keyword + bag-of-words cosine over a ~15-chunk corpus (stand-in for pgvector + tsvector) |
| Synthesis | ✅ **Real, dual-mode** — rule-based by default; real Claude API call with `--use-llm` |
| Citation verification | ✅ **Real** — tuple/ID matching + uncited-assertion regex scan |
| Confidence scoring | ✅ **Real** — exact weighted formula from ARCHITECTURE.md |
| Escalation routing | ✅ **Real** — same threshold and reason codes as the full design |
| TKRC directional match | ✅ **Real logic, toy dataset** — 5 classical formulations |
| Persistence, auth, PDF export, Freshness Monitor, Portfolio Mode | 🔲 Not implemented — full-system features, out of scope for PoC |

---

## Running the Project

### Option A — Web UI (recommended for demos)

Requires Flask. Install once:

```bash
pip install flask
```

Start the server:

```bash
cd prototype
python3 app.py
```

Open **http://localhost:5000** in your browser.

The UI has:
- One-click buttons for all 5 demo scenarios + the hallucination-catch demo
- Live stage-by-stage pipeline animation with spinners → checkmarks
- Expandable stage cards showing trace, retrieved chunks, citations
- Colour-coded roadmap with risk levels and verified citation chips
- Animated confidence score bar
- Escalation banner with reason code

---

### Option B — CLI

No dependencies required for the default rule-based mode (pure Python stdlib):

```bash
cd prototype
python3 main.py                          # run all 5 demo scenarios
python3 main.py --demo classical         # run one specific scenario
python3 main.py --demo phytopharma
python3 main.py --demo aahar
python3 main.py --demo patent_proprietary
python3 main.py --demo ambiguous
python3 main.py --demo bad-citation      # force a hallucinated citation — watch Stage 4 catch it
python3 main.py --formulation my.json   # run your own formulation file
```

Optional — real LLM synthesis (requires Anthropic API key):

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python3 main.py --use-llm
```

---

### Custom Formulation JSON

```json
{
  "ingredients": ["ashwagandha", "milk"],
  "extraction_method": "traditional decoction, sun-dried powder",
  "intended_use": "general wellness and stress support",
  "claims_text": "Rejuvenating tonic prepared following traditional method.",
  "jurisdiction": "IN"
}
```

Save as `my_formulation.json` and run:

```bash
python3 main.py --formulation my_formulation.json
```

---

## Demo Script (for Judges)

Run these three scenarios in order — each makes a distinct architectural point:

### 1. Classical — `--demo classical`
Shows a formulation correctly barred from a standard patent under §3(p) because it
matches documented traditional knowledge (Ashwagandha Churna, Charaka Samhita).
The system suggests a GI-route alternative and prints the TKRC directional match.
**Point to make:** The classification was done by pure logic — the LLM never touched it.

### 2. Ambiguous — `--demo ambiguous`
The formulation has an undisclosed blend and undefined use. The system refuses to guess
and routes directly to human escalation.
**Point to make:** Most AI tools would hallucinate an answer here. Saying "I don't know"
is a feature, not a failure.

### 3. Hallucination Catch — `--demo bad-citation`
The synthesis stage deliberately emits a citation to `Patents Act §3(k)` — a section
that was **never retrieved**. Stage 4 catches it:

```
✗ Step 2: cited Patents Act, 1970 3(k) (chunk_id=FABRICATED-NOT-RETRIEVED)
   — not present in the retrieved chunk set.
→ Verification failed. Retrying synthesis...
✓ All citations verified against retrieved chunks.  [on retry]
→ DELIVERED
```

**Point to make:** This is the architectural answer to "how do you prevent AI from
making up law?" The user never saw the hallucinated claim.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Pipeline logic | Pure Python (stdlib only) | Zero dependency for the core PoC |
| Web server | Flask | Minimal, SSE support, serves the HTML template |
| LLM (optional) | Anthropic Claude (via `anthropic` SDK) | Optional upgrade path for synthesis |
| Frontend | Vanilla HTML / CSS / JS | No build step, runs anywhere, looks premium |
| Full-scale target | Next.js + Postgres + pgvector + Clerk | Detailed in ARCHITECTURE.md |

---

## Scope & Disclaimer

IP-SAKTI is explicitly **not** a filing agent. It does not file anything with IPO, NBA,
or FSSAI, and does not claim to search TKDL. Every output carries an
_"informational, not legal advice"_ disclaimer. The goal is to replace the first
screening step — not to replace legal counsel.

---

## Team

Built for Smart India Hackathon 2026, problem statement **SIH26045**.
