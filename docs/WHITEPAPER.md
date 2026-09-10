# IP-SAKTI: An Ayurveda IP Navigator
### White Paper — Smart India Hackathon (SIH26045)

---

## Abstract

India's AYUSH sector produces thousands of new formulations every year, but the
overwhelming majority of individual formulators, small manufacturers, and student
innovators have no affordable way to answer a basic question before they spend
money: **"Can I even patent this — and if not, what can I actually do instead?"**

IP-SAKTI is a decision-support system that takes a formulation description in
natural language and returns a citation-verified, statute-grounded IP strategy
roadmap in minutes instead of weeks. It is built around one non-negotiable design
principle: **no legal claim is ever shown to a user unless it can be traced to a
specific, retrieved section of law.** This paper describes the problem, the system,
and why it is architecturally distinct from a conventional retrieval-augmented
chatbot.

---

## 1. The Problem

Ayurveda, Siddha, Unani, and Homeopathy (AYUSH) formulators sit at an unusual legal
intersection. A single formulation can simultaneously touch:

- The **Patents Act, 1970** (Section 3(p) bars patents on traditional knowledge)
- The **Biological Diversity Act, 2002** (NBA approval before filing, if biological
  resources are involved)
- The **Drugs & Cosmetics Act** and **FSSAI** rules (if positioned as a drug vs. a food)
- The **Geographical Indications Act** and trademark law (alternative protection
  routes when patenting is barred)
- International filing regimes, if the founder has export ambitions

Today, the only way to get a reliable answer that weaves all of this together is a
paid consultation with a patent attorney who specializes in AYUSH IP — a resource
that is scarce, expensive, and slow relative to how early-stage founders actually
work. The people this hurts most are exactly the people the AYUSH startup ecosystem
depends on: first-time innovators and small manufacturers who cannot absorb a
multi-week, multi-thousand-rupee consultation just to find out their idea is
already unpatentable.

Compounding the problem, the authoritative search tool patent examiners use for
this exact question — the **Traditional Knowledge Digital Library (TKDL)** — is
NDA-gated to patent offices by international agreement. It cannot be integrated
into a public tool, at any budget, by design. Any credible solution has to work
*around* that constraint, not pretend it doesn't exist.

## 2. Who This Is For

| User | Job to be done |
|---|---|
| Individual AYUSH formulators / student innovators | First-pass IP triage before they can afford an attorney |
| Small AYUSH manufacturers | Screening multiple product ideas quickly |
| AYUSH incubators & Technology Business Incubators (TBIs) | Screening applicant portfolios at scale |
| Patent agents | A fast, citation-backed first draft of the classification |

Patent examiners and large pharma companies are explicitly **not** the target —
they already have TKDL access and in-house counsel. IP-SAKTI's leverage is highest
for the underserved, first-time innovator, and that shapes every design decision
in this document.

## 3. What IP-SAKTI Does

Given a formulation description (ingredients, extraction method, intended use,
claims — in English or Hindi), the system:

1. **Classifies** it deterministically into one of five buckets: Classical,
   Patent & Proprietary, Phytopharmaceutical, Ayurveda Aahar, or **Ambiguous**.
2. **Retrieves** the specific statutory sections relevant to that classification
   and the user's chosen jurisdiction (India-only or India + International).
3. **Synthesizes** a structured roadmap: what's barred, what's viable, what
   regulatory approvals are needed before filing, and alternative protection
   routes (GI / Trademark / Design) if patenting is closed off.
4. **Verifies** every claim in that roadmap against the statutory text actually
   retrieved — rejecting and regenerating anything that can't be proven.
5. **Scores its own confidence** and routes low-confidence or ambiguous cases to
   a human reviewer network instead of guessing.
6. **Exports** a shareable PDF report, and **stays current** — if the underlying
   law changes, every affected prior analysis is flagged for re-review.

## 4. Why This Is Not "Just RAG"

A conventional retrieval-augmented generation pipeline retrieves relevant text and
asks a language model to answer from it. That architecture is a reasonable
starting point, but on its own it has no mechanism to *prove* its output is
correct — it trusts the model to cite honestly and hopes the retrieved context was
sufficient. For a domain where a wrong answer can cost a founder their IP
protection window, "hope" is not an acceptable failure mode.

IP-SAKTI diverges from basic RAG at four structural points:

**a) The highest-stakes decision is not made by the language model.**
Classification — the single decision that determines everything downstream — is
computed by a deterministic decision tree, not inferred by the LLM. The model's
role is strictly to explain and draft *around* a classification it did not choose.
This removes the one place a hallucination would be most damaging from the
model's control entirely.

**b) Citations are a verified gate, not a courtesy.**
The model must emit citations as structured data — `{act, section, chunk_id}` —
not free text. A separate verification step checks each citation against the
actual chunk IDs retrieved for that query. A secondary pattern scan catches
paraphrased legal assertions ("under Section...", "as per Rule...") that have no
matching citation entry, closing the gap a citations-array-only check would miss.
Any unverifiable claim triggers one corrective retry; a second failure routes to
human escalation — the user is never shown an unverified legal claim.

**c) "I don't know" is a designed output, not a failure state.**
When a formulation doesn't cleanly fit any bucket, the system returns
`classification = Ambiguous` and routes to escalation. This is a valid terminal
state with its own status and audit trail — most RAG systems force an answer from
whatever was retrieved rather than admitting the retrieval was insufficient.

**d) Answers are versioned and audited, not disposable.**
An Analysis is immutable once delivered. If the underlying statute changes, a new
Analysis supersedes the old one — the old one is never silently edited — and a
Freshness Monitor retroactively flags every prior analysis that relied on a
now-superseded section, offering the user one-click re-analysis. A basic RAG
chatbot has no concept of "this answer used to be true."

On top of this verification core, two domain-specific features push the system
further:

- **TKRC-aware directional signal** — TKDL itself is inaccessible, but the
  Traditional Knowledge Resource Classification (TKRC), the public, IPC-linked
  scheme built for exactly this kind of prior-art search, is not. Mapping a
  formulation to its TKRC code gives a defensible, non-hallucinated directional
  signal about Section 3(p) exposure — a feature that requires understanding the
  domain, not just retrieving more text.
- **Portfolio Mode** — turns a one-off query into tracked infrastructure an
  incubator can adopt for its whole applicant cohort, rather than a tool used
  once and abandoned.

## 5. System Architecture (Summary)

```
User → Intake & Language Detection
     → Deterministic Classification (pure logic, zero LLM, fully unit-testable)
     → Hybrid Retrieval (BM25 + vector, scoped to classification + jurisdiction)
     → LLM Synthesis (grounded strictly in retrieved chunks)
     → Citation Verifier (hard gate — reject & retry on any unverifiable claim)
     → Confidence Scoring & Escalation Routing
     → Delivered Analysis (PDF export) | Escalated to human review
```

Full technical detail — data model, API contract, failure modes, and tech stack
rationale — is maintained separately in `ARCHITECTURE.md`.

## 6. Scope Honesty

This system is explicitly **not** a filing agent. It does not file anything with
IPO, NBA, or FSSAI, and it does not claim to search TKDL. Every output carries an
"informational, not legal advice" disclaimer with a clear escalation path to a
human reviewer. The goal is to replace the *first screening step* that currently
costs a founder weeks and money — not to replace legal counsel.

## 7. Impact

For an individual formulator, IP-SAKTI compresses a multi-week, paid first
screening into a minutes-long, free, citation-backed answer. For an AYUSH
incubator, Portfolio Mode turns that into standing infrastructure for screening
an entire cohort. For the broader AYUSH innovation ecosystem, a system that is
honest about its own uncertainty — and that keeps itself current as law changes —
is a meaningfully more trustworthy foundation than a generic legal chatbot, and a
credible first step toward closing the access-to-IP-counsel gap for India's
smallest, least-resourced innovators.

## 8. Current Status

This white paper accompanies a working **proof-of-concept prototype** that
demonstrates the core verification loop described in Section 4 — deterministic
classification, scoped retrieval, citation-gated synthesis, and confidence-based
escalation — against a small, hand-curated statutory corpus. See `README.md` in
the prototype directory for setup and demo instructions, and `ARCHITECTURE.md`
for the full-scale system design this prototype is a proof for.
