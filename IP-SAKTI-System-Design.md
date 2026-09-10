# IP-SAKTI — System Design Document
### Ayurveda IP Navigator (SIH26045) — Senior Architecture Pass

Scope note: this is designed as a **36-hour SIH MVP with a credible path to a real product**, not a system already carrying production traffic. Phases below are sized accordingly — Phase 5 (capacity/latency) is treated lightly with an explicit "what changes at scale" callout, since the honest current load is "a demo judge and maybe 50 pilot users," not 10M DAU. Everything else (domain model, API contract, data flow, risk) is done at full depth because those decisions are hard to reverse later even in a prototype.

**Revision note**: this draft incorporates fixes from an independent architecture audit — corrected here: the idempotency constraint (was blocking the Freshness Monitor entirely), the Portfolio join table (was a jsonb array contradicting the doc's own relational-integrity rationale), an explicit `Ambiguous` classification terminal, an actual citation-verification protocol, a corrected PDF strategy (the original WeasyPrint choice was technically wrong — see Phase 4), and a rescoped, buildable Freshness Monitor. Two audit items — a job-queue lock-timeout reaper and rate-limiting on the public search endpoint — are accepted as correct but deliberately kept at backlog priority for the hackathon build specifically, since they're production-hardening concerns that don't match the "demo judge and ~50 pilot users" load this MVP is scoped for; do these before any real pilot, not before Sunday's demo.

**Second revision (re-audit pass)**: closed the dangling `/reanalyze` reference with a real endpoint; added `PATCH`/`DELETE` on formulations and analyses (the confidentiality-by-default promise in Phase 0 had no deletion mechanism to back it); defined the `confidence_score` formula and threshold (was referenced but never calculated); fixed a DFD/Phase-4 inconsistency (the diagram still said Qdrant/Chroma after the pgvector decision was made); specified the `RoadmapStep` schema explicitly (was implicit in an API example, needed by three different components that must agree on it); added a role model (`user | reviewer | incubator_admin | system_admin`) since "must own the resource" couldn't actually authorize the reviewer or incubator-admin use cases the doc itself described; mandated UUIDs on all public-facing IDs to close an IDOR path by construction; and made the prompt-injection defenses concrete (delimiters, input caps, output validation) rather than stated as a principle only.
	MedTech / BioTech / HealthTech

---

## PHASE 0 — Requirements Brief

### Functional scope

**In scope (MVP):**
- User submits a formulation description (ingredients, extraction method, intended use, claims) in natural language, in English or Hindi.
- System classifies the formulation (Classical / Patent & Proprietary / Phytopharmaceutical / Ayurveda Aahar) via a deterministic decision tree.
- System retrieves and cites the relevant statutory provisions (Patents Act, Biodiversity Act, Drugs & Cosmetics Act, FSSAI, GI Act, WIPO GRATK) for that classification.
- System produces a structured IP-strategy roadmap: what's barred, what's viable, what approvals are needed before filing (NBA Form 1/3), and alternative protection routes (GI/Trademark/Design) if patenting is barred.
- Every legal claim in the output must be traceable to a specific cited section/rule — no un-cited assertions.
- Jurisdiction toggle: India-only vs. India + International (WIPO/US FDA/EU pathway notes).
- Exportable PDF report of the analysis.

**Explicitly out of scope (MVP):**
- Actually filing anything with IPO/NBA/FSSAI — this is a decision-support tool, not a filing agent.
- Real-time TKDL search (TKDL access is NDA-gated to patent offices — cannot be integrated even if wanted).
- Legal representation or attorney-client-privileged advice — every output carries an "informational, not legal advice" disclaimer with an escalation path to a human.
- Multi-tenant enterprise billing/auth complexity — single simple auth model for the MVP.

### Who are the users
- **Primary**: individual AYUSH formulators, small manufacturers, and startup founders doing first-pass IP triage before they can afford a patent attorney.
- **Secondary**: AYUSH incubators/TBIs (Technology Business Incubators) screening applicant portfolios; patent agents wanting a fast first draft of the classification.
- **Not the primary user**: patent examiners (they have TKDL) or large pharma companies (they have in-house counsel) — the tool's leverage is highest for the underserved small/first-time innovator, which should shape tone and pricing later.

### Core job to be done
Given a described formulation, tell the user **within minutes, with citations, whether they can patent it — and if not, what they can do instead** — replacing what today takes a costly, multi-week attorney consultation as the *first* screening step.

### Non-functional constraints

| Constraint | Target | Why |
|---|---|---|
| Scale (hackathon) | ~10–50 concurrent demo/pilot users | Real number for SIH; don't over-engineer |
| Scale (1–2yr, if adopted by an AYUSH incubator) | ~500–5,000 registered users, low concurrency (this is a research/triage tool, not a consumer app — usage is bursty, not constant) | Sets realistic ceiling: a single well-sized Postgres + a vector index handles this comfortably; no need for distributed infra |
| Latency | p95 < 8s for a full classification+citation response (LLM-in-the-loop, so this is *not* a sub-second API) | User is doing research, not swiping a feed — a few seconds is acceptable if content is trustworthy |
| Consistency | Strong consistency on the statutory corpus (never serve a stale/removed section); eventual consistency acceptable for usage analytics | Legal correctness > analytics freshness |
| Availability | Best-effort for MVP (single region, no HA requirement for a hackathon demo); 99% target if it becomes a pilot product | Downtime cost is reputational, not financial, at this stage |
| Read/write ratio | Extremely read-heavy (95%+ reads: users query, rarely write beyond account/portfolio data) | Confirms read-optimized architecture: cache aggressively, no write-heavy infra needed |
| Compliance | No PII beyond email/name for auth; formulation descriptions may be commercially sensitive (treat as confidential-by-default, no cross-user data sharing without explicit opt-in) | Users are disclosing trade-secret-adjacent formulation details — a real trust boundary, not boilerplate |

**Assumption flagged**: I'm assuming pilot-stage usage (hundreds, not millions, of users) based on the niche AYUSH-innovator audience described in the problem statement — flag if your team is scoping this for a broader consumer launch, since that would change the stack conversation materially.

---

## PHASE 1 — Domain Model

### Ubiquitous language (glossary)
- **Formulation** — the ingredient/method/claim combination a user is asking about.
- **Classification** — the deterministic bucket a Formulation falls into (Classical / P&P / Phytopharmaceutical / Aahar).
- **Statutory Chunk** — an indexed, citable unit of legal text (a section, sub-clause, or rule) from the corpus.
- **Analysis** — the full output object: Classification + cited Statutory Chunks + Roadmap + Confidence Score.
- **Roadmap Step** — one actionable recommendation inside an Analysis (e.g., "File NBA Form 3 before patent filing").
- **Jurisdiction** — India-only or India+International; changes which Statutory Chunks are eligible for retrieval.
- **Escalation** — a flagged Analysis (low confidence or high-stakes) routed toward human review (patent agent / AYUSH law clinic partner).
- **Portfolio** *(differentiation feature, see below)* — a user's saved collection of Formulations tracked over time.

### Core entities & lifecycle

```
User ──creates──> Formulation ──produces──> Analysis ──cites──> StatutoryChunk[]
                                     │
                                     └──contains──> RoadmapStep[]

Formulation lifecycle:  Draft → Classified → Analyzed → (Reviewed by human, optional) → Archived
Analysis lifecycle:     Generated → Delivered → (Escalated | Accepted) → Superseded (if statute changes — see Freshness Monitor below)

Classification enum (corrected): Classical | Patent&Proprietary | Phytopharmaceutical | Aahar | **Ambiguous**
  — Ambiguous is not a failure state, it's a valid terminal: the decision tree can legitimately fail to cleanly bucket an input,
    and an Analysis with classification=Ambiguous is created with status=escalated rather than leaving no valid row at all.

Analysis status enum (corrected): queued → processing → synthesizing → delivered | escalated
  — "queued" (job accepted, worker hasn't picked it up) is distinct from "processing" (worker actively running the pipeline) —
    without this distinction a stuck queue and a slow-but-healthy pipeline look identical from the outside.
```

### Invariants (must always hold)
1. Every `RoadmapStep` inside an `Analysis` must reference at least one `StatutoryChunk` — **no un-cited recommendation is ever returned to the user.** This is the single most important business rule in the whole system (it's the difference between IP-SAKTI and a generic legal chatbot).
2. A `Formulation`'s `Classification` is deterministic given the same inputs — the decision tree (Phase logic, not the LLM) owns classification; the LLM only explains and drafts around a classification it did not itself decide. This keeps the highest-stakes decision out of LLM hallucination risk.
3. An `Analysis` is immutable once delivered (for audit purposes) — if the underlying law changes, a **new** Analysis supersedes it; the old one is never silently edited.
4. `Jurisdiction = International` analyses must never omit the India-domestic layer — international guidance is additive, not a replacement.

### ER Diagram

```
┌─────────────────┐       ┌──────────────────────┐       ┌───────────────────┐
│      User        │       │      Formulation      │       │      Analysis       │
├─────────────────┤       ├──────────────────────┤       ├───────────────────┤
│ id (PK)           │1     │ id (PK)                 │1     │ id (PK)               │
│ email             │──────│ user_id (FK)            │──────│ formulation_id (FK)   │
│ name              │  *    │ ingredients (jsonb)     │  *    │ classification (enum) │
│ org (nullable)     │      │ extraction_method       │      │ confidence_score       │
│ role (enum)        │      │ intended_use            │      │ roadmap (jsonb)        │
│ created_at         │      │ claims_text             │      │ jurisdiction (enum)    │
└─────────────────┘       │ status (enum)           │      │ status (enum)          │
                             │ created_at              │      │ superseded_by (FK, null)│
                             └──────────────────────┘      │ created_at             │
                                                                └─────────┬─────────┘
                                                                            │ *
                                                                            ▼
                                                                ┌────────────────────────┐
                                                                │  AnalysisCitation        │  (join table)
                                                                ├────────────────────────┤
                                                                │ analysis_id (FK)          │
                                                                │ statutory_chunk_id (FK)   │
                                                                │ relevance_score           │
                                                                └───────────┬────────────┘
                                                                            │ *
                                                                            ▼
                                                                ┌────────────────────────┐
                                                                │   StatutoryChunk          │
                                                                ├────────────────────────┤
                                                                │ id (PK)                   │
                                                                │ act_name                  │
                                                                │ section_number            │
                                                                │ text_content               │
                                                                │ effective_date             │
                                                                │ superseded_date (nullable) │
                                                                │ source_gazette_url         │
                                                                │ embedding (vector)          │
                                                                └────────────────────────┘

┌────────────────────┐  ┌──────────────────────────┐        ┌───────────────────────┐
│    Portfolio          │  │ PortfolioFormulation        │        │   EscalationRequest       │
├────────────────────┤1 │ (join table — FK, not jsonb)│        ├───────────────────────┤
│ id (PK)                 │──│ portfolio_id (FK)          │        │ id (PK)                    │
│ user_id (FK)            │* │ formulation_id (FK)        │        │ analysis_id (FK)           │
│ name                    │  │ added_at                    │        │ created_by (FK→User, null) │
│ created_at              │  └──────────────────────────┘        │ reason (enum, incl.        │
└────────────────────┘                                          │   system_citation_failure, │
                                                                     │   system_unavailable)      │
                                                                     │ assigned_reviewer (nullable)│
                                                                     │ status (enum)               │
                                                                     └───────────────────────┘
```

---

## DATA FLOW DIAGRAMS

### DFD — Level 0 (Context Diagram)

```
                    ┌──────────────────────────────────────────┐
                    │                                            │
   ┌──────────┐     │                                            │     ┌────────────────────┐
   │   User    │────▶│                                            │────▶│  Statutory Corpus    │
   │(Innovator)│◀────│              IP-SAKTI SYSTEM                │◀────│  (Acts/Rules/Gazette)│
   └──────────┘     │                                            │     └────────────────────┘
                    │                                            │
   ┌──────────┐     │                                            │     ┌────────────────────┐
   │  Patent   │◀────│                                            │────▶│  LLM Provider (API)  │
   │Agent/Clinic│    │                                            │     └────────────────────┘
   └──────────┘     │                                            │
                    │                                            │     ┌────────────────────┐
                    │                                            │────▶│  Bhashini (translate) │
                    └──────────────────────────────────────────┘     └────────────────────┘
```

### DFD — Level 1 (Decomposed)

```
[User] ──(1) Formulation description──▶ ┌─────────────────────┐
                                          │ P1: Intake &         │
                                          │ Language Detection    │
                                          └──────────┬──────────┘
                                                     │ normalized text
                                                     ▼
                                          ┌─────────────────────┐         ┌───────────────┐
                                          │ P2: Deterministic     │────────▶│ D1: Formulation │
                                          │ Classification Wizard │         │ Store (Postgres)│
                                          └──────────┬──────────┘         └───────────────┘
                                                     │ classification label
                                                     ▼
                                          ┌─────────────────────┐         ┌───────────────┐
                                          │ P3: Hybrid Retrieval  │◀───────▶│ D2: Statutory   │
                                          │ (BM25 + Vector)        │         │ Chunk Index      │
                                          └──────────┬──────────┘         │ (pgvector — see  │
                                                     │ ranked chunks              │  Phase 4; not a  │
                                                     │                              │  separate DB)    │
                                                     ▼                              └───────────────┘
                                                     ▼
                                          ┌─────────────────────┐         ┌───────────────┐
                                          │ P4: LLM Synthesis &   │────────▶│ External:        │
                                          │ Roadmap Generation      │◀───────│ LLM Provider API  │
                                          └──────────┬──────────┘         └───────────────┘
                                                     │ draft analysis
                                                     ▼
                                          ┌─────────────────────┐
                                          │ P5: Citation Verifier │
                                          │ (reject un-cited claims)│
                                          └──────────┬──────────┘
                                             pass │       │ fail → loop back to P4 (max 2 retries)
                                                     ▼
                                          ┌─────────────────────┐         ┌───────────────┐
                                          │ P6: Confidence Scoring│────────▶│ D3: Analysis     │
                                          │ & Escalation Routing   │         │ Store (Postgres)│
                                          └──────────┬──────────┘         └───────────────┘
                                          low conf │       │ normal
                                                     ▼            ▼
                                     ┌───────────────┐   ┌─────────────────┐
                                     │ P7: Escalation  │   │ P8: PDF Report &  │
                                     │ Queue (human    │   │ Response Delivery  │
                                     │ review)         │   └────────┬────────┘
                                     └───────────────┘                    ▼
                                                                    [User receives Analysis]
```

**Where hidden coupling would normally hide, made explicit**: P5 (Citation Verifier) is a hard gate, not a soft check — if the LLM's draft references a section not present in the retrieved chunk set from P3, it is rejected and regenerated (bounded at 2 retries, then routed to P7 Escalation rather than ever shown un-cited to a user). This is the single design decision that turns this from "a chatbot that could hallucinate law" into a system with an enforced factuality boundary — and it belongs in the answer to any judge who asks "how do you prevent hallucination."

**Citation protocol (specified, not left to "string matching" — this is the single most important spec in the whole document since it implements Invariant #1):**
1. The LLM's system prompt mandates a structured output: the natural-language roadmap text *plus* a parallel `citations` JSON array, e.g. `{"citations": [{"act": "Patents Act, 1970", "section": "3(p)", "chunk_id": "..."}]}`. The model cites structured fields, not free text.
2. The verifier matches each cited `(act, section)` tuple against the `(act_name, section_number)` fields of the chunks actually retrieved in P3 — not a fuzzy string match, a field match against known-good IDs.
3. **Uncited-claim scan**: a secondary regex/pattern check runs over the roadmap text for legal-assertion markers ("under Section", "pursuant to", "as per Rule", "barred by") that have no corresponding entry in the `citations` array — this catches paraphrased claims that would otherwise sail past a citations-array-only check.
4. Any failure (unmatched citation *or* an uncited assertion) triggers one retry with an explicit correction prompt listing exactly which claims failed; a second failure routes to Escalation with `reason = system_citation_failure` — never shown to the user unverified.

**Confidence score (P6 — previously an undefined field, now specified):**
```
confidence = 0.5 × citation_pass_rate            # fraction of roadmap claims that verified on the first pass, no retry needed
           + 0.3 × avg_retrieval_relevance         # mean relevance score of the chunks P3 actually retrieved
           + 0.2 × classification_certainty        # 1.0 if the decision tree hit a clean terminal, 0.0 if it landed on Ambiguous
```
Escalation threshold: `confidence < 0.5` → auto-route to Escalation (`reason = low_confidence`) even if citation verification technically passed — a low score means the *retrieval* was thin (few relevant chunks found), which is a real signal worth a human look even without a hard citation failure.

---

## PHASE 2 — API Contract

**Style choice**: REST, sync request/response for the core analysis flow (user is waiting, few-second latency is acceptable), with a light async pattern for the PDF export job (can be slow, no reason to hold a connection open).

```
POST /api/v1/formulations
  Auth: required (Bearer JWT)
  Body: { ingredients: string[], extraction_method: string, intended_use: string, claims_text: string, jurisdiction: "IN" | "IN_INTL", language: "en" | "hi" }
  201 → { formulation_id, status: "draft" }
  400 → { error: "validation_error", fields: [...] }

POST /api/v1/formulations/{id}/analyze
  Auth: required, must own formulation_id
  202 → { analysis_id, status: "processing" }   # async — LLM step can exceed a sync timeout comfortably
  409 → { error: "already_analyzed", analysis_id, reanalyze_url: "/api/v1/formulations/{id}/reanalyze" }

POST /api/v1/formulations/{id}/reanalyze
  Auth: required, must own formulation_id
  Body: { reason: "user_requested" | "statute_updated" }   # statute_updated is set by the Freshness Monitor's admin trigger, not typed by the user
  202 → { analysis_id, status: "processing", supersedes: <previous_analysis_id> }
  # Creates a NEW Analysis row (superseded_by on the old one), never edits the old one — matches Invariant #3 (immutability)

PATCH /api/v1/formulations/{id}
  Auth: required, must own; only while status="draft" (a formulation already analyzed is not edited in place — reanalyze instead, so an Analysis's citations always trace to the exact input that produced them)
  200 → { formulation_id, status: "draft" }

DELETE /api/v1/formulations/{id}
  Auth: required, must own
  204 → (soft delete; existing Analyses are archived, not deleted, for audit continuity — but the source Formulation text is purged, honoring the confidentiality-by-default promise in Phase 0)

DELETE /api/v1/analyses/{id}
  Auth: required, must own
  204 → (marks archived; underlying corpus citations are untouched — this only affects the user's own record)

GET /api/v1/analyses/{id}
  200 → {
    analysis_id, formulation_id, classification, confidence_score,
    roadmap: [ { step, action, citations: [{act, section, url}], risk_level } ],
    jurisdiction, status: "delivered" | "escalated" | "processing",
    disclaimer: "Informational only, not legal advice."
  }
  404 → { error: "not_found" }

GET /api/v1/analyses/{id}/export.pdf
  200 → binary PDF

POST /api/v1/escalations
  Body: { analysis_id, reason: "low_confidence" | "user_requested" | "high_stakes" | "system_citation_failure" | "system_unavailable" }
  201 → { escalation_id, status: "queued" }

GET /api/v1/escalations/{id}
  Auth: required — owner of the underlying analysis OR the assigned_reviewer (see role model below)
  200 → { escalation_id, analysis_id, reason, status, assigned_reviewer }

GET /api/v1/escalations
  Auth: required — returns the caller's own escalations (as owner) or assigned ones (as reviewer), cursor-paginated

# ID format: all public-facing IDs (formulation_id, analysis_id, escalation_id, portfolio_id) are UUIDv4, never
# auto-incrementing integers — sequential IDs on user-owned resources are enumerable and become an IDOR vector
# the moment auth has any gap; UUIDs cost nothing here and close that class of bug by construction.

# Role model (User.role, previously undefined):
#   user            — owns and accesses only their own formulations/analyses/portfolios
#   reviewer        — read access to analyses/escalations where they are the assigned_reviewer; no ownership needed
#   incubator_admin — read/manage formulations for users who've explicitly linked their account to that org
#   system_admin    — full access; the only role that can trigger the Freshness Monitor's manual corpus-update flow

# RoadmapStep schema (the core output the user reads — was implicit, now explicit):
#   class RoadmapStep(BaseModel):
#       step: int                                          # ordinal position
#       action: str                                        # what to do
#       rationale: str                                      # why, in plain language
#       citations: list[Citation]                           # from the citation protocol above — never empty (Invariant #1)
#       risk_level: Literal["low", "medium", "high", "blocker"]
#       timeline_note: str | None = None                    # e.g. "before patent filing"
#   This schema is the contract between the LLM prompt template, the citation verifier, and the frontend —
#   all three must agree on these field names, which is why it's specified once here rather than three times.

GET /api/v1/statutes/search?q=...&jurisdiction=IN
  200 → { chunks: [{act, section, text_snippet, relevance_score}] }   # transparency endpoint — lets a user or judge inspect the corpus directly

# Differentiation-feature endpoints (see recommendations section):
POST /api/v1/portfolios                          # group formulations for a startup/incubator
GET  /api/v1/statutes/changes?since=DATE          # freshness monitor feed
POST /api/v1/formulations/{id}/compare            # multi-formulation IP-route comparator
GET  /api/v1/gi/overlap?region=...&product=...    # GI-cluster conflict checker
```

**Error taxonomy**: `4xx` = client-fixable (bad input, not-owned resource, already-exists) → not retryable without change; `5xx` = system fault (LLM provider down, index unreachable) → retryable with backoff. `202` (accepted) is used deliberately for the analyze step so a slow LLM call never holds a client connection open or times out a load balancer.

**Auth boundary**: JWT-based user auth on every mutating and every user-scoped read; the `/statutes/search` transparency endpoint is intentionally public/unauthenticated (no sensitive data, and public inspectability of the corpus is itself a trust feature — a judge or skeptical user can verify the system isn't inventing law).

---

## PHASE 3 — Data Flow & Lifecycle Trace

### Happy path: "Classify my Ashwagandha extract"

1. **Entry**: `POST /formulations` → auth middleware validates JWT → input validation (ingredients non-empty, claims_text present) → row inserted in `formulations` (status=`draft`). *Owns this step: API layer.*
2. **Trigger**: `POST /formulations/{id}/analyze` → enqueues an async job (simple job queue, not a heavyweight broker — see Phase 4) → returns `202` immediately with `analysis_id`, status=`processing`. *Owns this step: API layer + job queue.*
3. **Classification (P2)**: worker runs the deterministic decision tree (pure function, no LLM) against the formulation fields → produces a `classification` enum value. *Owns this step: business logic module, fully unit-testable in isolation.*
4. **Retrieval (P3)**: worker queries the vector+BM25 hybrid index scoped to `(classification, jurisdiction)` → returns top-k `StatutoryChunk`s with relevance scores. *Owns this step: retrieval module.*
5. **Synthesis (P4)**: worker calls the LLM provider with the retrieved chunks injected as grounding context + a strict system prompt ("cite only from provided context; if the context doesn't support a claim, say so explicitly rather than inferring"). *Owns this step: LLM orchestration module — this is the only step with a genuine external dependency and the only step that can meaningfully fail unpredictably.*
6. **Citation Verification (P5)**: worker parses the LLM's cited section numbers, checks each against the actual retrieved chunk set (string/ID match, not LLM-judged) → if any citation is unverifiable, retry P4 once with an explicit correction prompt; second failure routes straight to P7 (Escalation) instead of ever showing the user an unverified claim.
7. **Persistence**: analysis row written to `analyses` (status=`delivered` or `escalated`), citation join rows written to `analysis_citations`. *Source of truth: Postgres — this is the one place "what did we actually tell this user" lives, which matters for audit/liability.*
8. **Response**: user polls `GET /analyses/{id}` (or receives a webhook/websocket push in a v2) until status flips from `processing` to `delivered`.

### Failure path: LLM provider is down or times out

- Job queue's retry policy: 3 attempts with exponential backoff (2s/8s/30s) before marking the job `failed`.
- On `failed`, `analysis.status` becomes `escalated` (reason=`system_unavailable`) rather than silently erroring — the user always gets *some* forward path (a human will look at it), never a dead end.
- Idempotency: the constraint lives on the **job table**, not the `Analysis` table — `UNIQUE (formulation_id, jurisdiction) WHERE status IN ('queued','processing')` as a partial index. This blocks duplicate *in-flight* jobs (redelivery, double-click) without blocking legitimate re-analysis later (Freshness Monitor re-runs, user-requested re-analysis). Multiple completed `Analysis` rows can and should exist for the same `(formulation_id, jurisdiction)` pair over time, linked via `superseded_by`. *(Corrected from an earlier draft that put a blanket unique constraint on the Analysis table — that would have silently blocked the Freshness Monitor and any re-analysis flow.)*
- Partial failure inside P4/P5 (LLM responds but citation check fails twice): same escalation path, reason=`system_citation_failure` — this is actually a *good* failure mode to be able to demo to judges (shows the system catching its own potential hallucination rather than shipping it).

---

## PHASE 4 — Tech Stack Decisions

| Component | Options considered | Choice | Why (tied to Phase 0) |
|---|---|---|---|
| Primary datastore | Postgres, MongoDB | **Postgres** | Relational integrity matters here (Formulation→Analysis→Citation is a real referential chain you want FK constraints on, not app-level enforcement); `jsonb` columns give document-like flexibility for `ingredients`/`roadmap` fields without giving up transactions |
| Vector index | Qdrant, Chroma, pgvector | **pgvector (Postgres extension)** for MVP, not a separate vector DB | At this data volume (a few thousand statutory chunks, not millions), a separate vector database is premature infrastructure — pgvector keeps the whole stack to one database, one backup story, one ops surface. Revisit only if corpus grows past ~100K chunks or query latency becomes the bottleneck. |
| Keyword search (BM25 side of hybrid) | Elasticsearch, Postgres full-text search | **Postgres full-text search (tsvector)** | Same reasoning — one datastore for a dataset this size beats standing up Elasticsearch for a corpus that fits comfortably in Postgres |
| LLM provider | GPT-4o, Gemini 1.5 Pro, Claude, open-source local model | **Any strong instruction-following model via a provider-agnostic wrapper (LiteLLM)** | Don't hard-lock to one vendor for a legal-accuracy-critical system — provider outages/pricing changes shouldn't be an architecture-level risk; abstract behind one interface |
| Job queue | Kafka, RabbitMQ, Postgres-backed queue (e.g., `pg-boss`/simple table+polling) | **Postgres-backed simple queue** | At this scale (dozens of concurrent analyses, not thousands/sec), a dedicated message broker is a distributed-systems tax with no payoff — one job table with `status`/`locked_at` columns and a polling worker is enough, and it's one less system to operate for a 4-person hackathon team |
| Auth | Build custom, Auth0/Clerk, Supabase Auth | **Managed auth provider (Clerk/Supabase Auth)** | Don't build auth for a hackathon MVP — zero unique value in rolling your own, real security risk in doing it badly under time pressure |
| Frontend | Next.js, Streamlit | **Next.js + Tailwind** for the real demo (per the original blueprint) — Streamlit acceptable only as an hour-zero fallback if the team is frontend-light | Next.js gives a genuinely presentable, judge-facing UI; Streamlit is faster to stand up but reads as "hackathon prototype" rather than "product" — worth the extra hours if the team can spare them |
| PDF export | ReportLab, headless-Chrome/Puppeteer print, WeasyPrint, `@react-pdf/renderer` | **`@react-pdf/renderer` (client-side, in the Next.js app)** | *(Corrected — an earlier draft claimed WeasyPrint could reuse the React report template; that's wrong, WeasyPrint has no JS runtime and cannot render React. Rendering the PDF client-side with `@react-pdf/renderer` genuinely shares component logic with the on-screen view and needs no extra backend service — the simplest correct option for a hackathon.)* |
| Translation (Hindi UI/queries) | Google Translate API, Bhashini | **Bhashini** | Government-backed, free-tier friendly for a hackathon, and using India's own public digital infrastructure is a legitimately good India-specific-advantage story for judges, not just a cost decision |

**Build vs. buy calls made explicitly**: auth = buy (Clerk/Supabase), vector search = borrow (pgvector, not a new service), translation = borrow (Bhashini, public infra), job queue = build-light (a Postgres table is "building" but it's 50 lines, not a new system) — the only genuinely custom, hard-to-buy piece is the classification decision tree + citation verifier, which is exactly where the team's engineering effort should concentrate, because that's the part that's actually the product.

---

## PHASE 5 — Capacity & Latency (lightweight, hackathon-scoped)

**Honest current numbers**: tens of concurrent users at a demo, low hundreds if piloted with one AYUSH incubator. This does not justify horizontal scaling, sharding, or a CDN-fronted multi-region deployment — building for that now would be premature-abstraction, one of the exact anti-patterns this process warns against.

**Latency budget for the p95 target (~8s)**:
- Auth + validation: ~50ms
- Classification (pure logic, no I/O beyond one DB read): ~20ms
- Hybrid retrieval (pgvector + tsvector query): ~200–400ms
- LLM synthesis call: **~4–7s** — this dominates the budget and is the one component genuinely outside your control; stream the response to the frontend (token-by-token) so perceived latency is much lower than actual latency, even though this doesn't change the real number
- Citation verification (string matching against retrieved chunk IDs, no extra LLM call needed): ~10ms
- PDF export: async, off the critical path entirely

**What changes at real scale** (documented for the "scalability slide" judges will ask about, not built now): if this becomes a genuine national AYUSH-sector tool — separate the vector index out of Postgres into Qdrant once chunk count or QPS makes `pgvector` the bottleneck; move the job queue to a real broker once concurrent analysis volume exceeds what table-polling can serve without contention; add a read replica once the `/statutes/search` transparency endpoint gets meaningful public traffic (it's the one endpoint that could see genuinely unpredictable load, since it's unauthenticated and linkable).

---

## PHASE 6 — Architecture Pattern & Module Map

**Pattern chosen: modular monolith.** This is not a resume-driven microservices system — a 4-person hackathon team with one deployable target, one datastore, and a workload that's fundamentally "one request triggers one linear pipeline" gets nothing from service decomposition except deployment complexity. Modules are separated by *code boundary*, not *network boundary*.

```
Request → API Layer (routes/controllers, auth, validation)
             ↓
          Service Layer (business logic — classification, orchestration, escalation rules)
             ↓
          Domain Modules (deep, single-responsibility):
             - classifier/        (pure decision-tree logic, zero I/O, fully unit-testable)
             - retrieval/         (hybrid search — the only module touching the vector index)
             - synthesis/         (LLM orchestration + prompt templates)
             - citation_verifier/ (the trust boundary — verifies before anything reaches a user)
             - escalation/        (routing to human review)
             ↓
          Repository Layer (Postgres access, one repo per aggregate: FormulationRepo, AnalysisRepo, StatutoryChunkRepo)
             ↓
          Storage (Postgres + pgvector)
```

**The deletion test applied**: if you removed `citation_verifier/` as a separate module and inlined its check into `synthesis/`, the complexity wouldn't disappear — it'd just be harder to test in isolation and easier to accidentally skip under time pressure. It earns its place as a separate, mandatory module. Conversely, don't create a separate microservice for `escalation/` — it's simple enough to be a service-layer concern, not a whole deployable.

**Seams deliberately not built yet**: no adapter interface for "swap the vector DB" — you have one implementation (pgvector) and no second one coming imminently; wrap it cleanly in `retrieval/` but don't build a plugin architecture for a hypothetical Qdrant migration that isn't scheduled.

---

## PHASE 7 — Risk, Failure Modes & Observability

| Failure mode | Likelihood × Impact | Detection | Mitigation |
|---|---|---|---|
| LLM hallucinates a section number / misstates the law | Medium × **Critical** | Citation Verifier catches unverifiable citations before delivery (P5) | Hard gate, not advisory — never bypass this even under demo time pressure |
| Statutory corpus goes stale (an Act is amended, e.g., the 2023 Biodiversity Amendment) | Medium × High | Freshness Monitor (see recommendations) diffs against Gazette feed | Superseded-chunk flagging + re-analysis prompt to affected users |
| LLM provider outage/rate-limit mid-demo | Low (demo window) × High (demo-killing) | Provider health check before demo starts; LiteLLM's provider-agnostic wrapper allows failover to a second provider | Have a secondary LLM provider configured and tested before judging, not discovered live |
| User submits a formulation with sensitive/trade-secret detail and worries about confidentiality | Medium × Medium (trust, not technical) | N/A — this is a policy question | Explicit no-cross-user-sharing statement, and for the real pilot, a data-retention/deletion policy stated up front |
| Deterministic classifier's decision tree has an edge case (formulation doesn't cleanly fit any of the 4 buckets) | Medium × Medium | Low-confidence fallback path | Route to "Ambiguous — Escalated" rather than forcing a wrong bucket; this is a legitimate output, not a bug, and worth demoing as evidence of honesty |

**Minimal observability (the vital few, not everything)**:
- LLM call latency + error rate (the one external dependency most likely to misbehave)
- Citation-verification pass/fail rate (a rising fail rate is the single best signal that the corpus or prompt has drifted and needs attention)
- Escalation queue depth (tells you, at a glance, whether the automated path is actually covering most traffic or whether it's silently failing over to humans too often)

**Security boundaries flagged for a focused pass**: JWT validation on every mutating endpoint; formulation text is user-supplied and flows into an LLM prompt — standard prompt-injection hygiene applies (never let retrieved/user content be interpreted as system instructions; keep the "cite only from provided context" instruction in the system role, not concatenated into user content).

**Made concrete (previously stated as a principle without a spec):**
- `claims_text` and `ingredients` are placed **only in the user message**, wrapped in explicit delimiters: `<formulation>{claims_text}</formulation>`. The system prompt states plainly that content inside those tags is data, never instructions, regardless of what it claims to be.
- Input caps enforced before the request ever reaches the LLM or the queue: `claims_text` ≤ 3,000 characters; `ingredients` ≤ 100 items, each ≤ 200 characters. This isn't primarily about injection (jsonb storage is already parameterized, so there's no SQL-injection path) — it's about resource exhaustion: an unbounded array turns into an unbounded prompt, which turns into unbounded LLM cost and latency per request.
- Output validation as a second line of defense beyond the Citation Verifier: if the LLM's response contains no valid `classification` value at all, reject immediately without spending a retry — that shape of failure means the model was steered off-task entirely, and a correction-prompt retry is unlikely to recover it.
- Team should explicitly red-team this before demo day — have someone try an "ignore previous instructions" payload in `claims_text` live, once, before a judge does it for you.

---

## PROJECT STRUCTURE

```
ip-sakti/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── routes/
│   │   │   ├── formulations.py
│   │   │   ├── analyses.py
│   │   │   ├── escalations.py
│   │   │   ├── statutes.py
│   │   │   └── portfolios.py         # differentiation feature
│   │   ├── services/
│   │   │   ├── analysis_orchestrator.py
│   │   │   └── escalation_router.py
│   │   ├── domain/
│   │   │   ├── classifier/
│   │   │   │   └── decision_tree.py
│   │   │   ├── retrieval/
│   │   │   │   └── hybrid_search.py
│   │   │   ├── synthesis/
│   │   │   │   ├── prompts.py
│   │   │   │   └── llm_client.py
│   │   │   └── citation_verifier/
│   │   │       └── verifier.py
│   │   ├── repositories/
│   │   │   ├── formulation_repo.py
│   │   │   ├── analysis_repo.py
│   │   │   └── statutory_chunk_repo.py
│   │   ├── workers/
│   │   │   └── analysis_worker.py    # polls job table, runs pipeline
│   │   └── main.py
│   └── web/                          # Next.js frontend
│       ├── app/
│       │   ├── formulation/new/
│       │   ├── analysis/[id]/
│       │   └── portfolio/
│       └── components/
│           ├── JurisdictionToggle.tsx
│           ├── FormulationWizard.tsx
│           ├── CitationCard.tsx
│           └── FreshnessAlertBanner.tsx   # differentiation feature
├── data/
│   ├── raw_statutes/
│   ├── processed_chunks/*.jsonl
│   └── classical_texts_index.json
├── scripts/
│   ├── ingest_corpus.py
│   └── reindex.py
├── tests/
│   ├── domain/test_classifier.py     # pure-logic tests, no mocks needed
│   ├── domain/test_citation_verifier.py
│   └── integration/test_golden_scenarios.py
└── infra/
    └── docker-compose.yml            # postgres+pgvector, api, worker, web — one command, one machine
```

---

## ADDITIONAL FUNCTIONALITY — RECOMMENDATIONS TO MAKE THIS MORE UNIQUE, DIFFERENTIATED, AND USEFUL

The original blueprint (classify → cite → roadmap) is solid but is still, structurally, a Q&A tool — ask once, get an answer once. The recommendations below are chosen specifically to push it from "smart search over a legal corpus" toward "a system that produces an outcome and stays useful over time," which is exactly the distinction the evaluation framework's AI-chatbot-rejection test is looking for. I've prioritized ones that are genuinely buildable in the SIH timeframe, and flagged the one that's a stretch.

### 1. Freshness Monitor (highest-priority addition — MVP scope corrected)
The Cabinet has already approved widening TKDL access — meaning the regulatory ground here is actively shifting. **For the 36-hour build, this must be a manual admin-triggered flow, not an automated scraper**: eGazette publishes amendment notifications as PDFs with no structured API, and India Code has no amendment feed either — automated diffing against either source is a real post-MVP project, not a hackathon task. The buildable version: an admin uploads a revised version of a tracked Act/section, the system diffs it chunk-by-chunk against the existing corpus, marks the old chunk `superseded_date`, and **flags every prior Analysis that cited it**, offering a one-click re-analysis. This still delivers the demo moment ("watch what happens when we simulate an amendment to Section 3(p)") without requiring a scraper the team can't realistically build and validate in the time available. Document automated Gazette monitoring explicitly as a post-MVP roadmap item when pitching to judges — overclaiming automation here is a credibility risk if a judge asks "show me it detecting a real amendment right now."

### 2. Portfolio Mode (turns single queries into a retained product)
Let a formulator or an AYUSH incubator register a **portfolio** of formulations rather than one-off queries, with a dashboard view: classification distribution, how many are IP-viable vs. GI/trademark-routed vs. escalated, and portfolio-wide freshness status. This is the difference between a tool someone uses once and a tool an incubator adopts as ongoing infrastructure for screening its cohort — a much stronger "why would BIS/AYUSH ministry actually adopt this" story than a stateless chatbot.

### 3. NBA Form 3 / Trademark Application Draft Pre-fill
Don't just tell the user "you need to file NBA Form 3 before patenting" — **auto-populate a draft of Form 3** (applicant details, biological resource description, origin) from data already captured in the Formulation intake, so the user reviews and completes rather than starting from a blank government form. This is the single change that would most convincingly answer the master-prompt's "AI must produce a meaningful outcome, not just information" test — it moves the system from advisory to action-adjacent, without ever actually filing anything on the user's behalf (keeps the "informational only" liability boundary intact — you're pre-filling a draft, not submitting).

### 4. TKRC-Aware Directional Novelty Pre-Check
TKDL itself is inaccessible, but the **Traditional Knowledge Resource Classification (TKRC)** — the public, IPC-linked classification scheme built specifically so patent offices can search TKDL — has published, publicly available classification codes and structure. Integrating TKRC codes into the classifier lets the system give a *directional* signal ("your formulation maps to TKRC code [X], associated with classical texts in category [Y] — high likelihood of Section 3(p) exposure") without ever claiming to search TKDL itself. This is a genuinely hard-to-replicate feature because it requires someone to have actually understood TKRC's structure, not just "add more RAG" — worth calling out explicitly to judges as the one piece of domain engineering a generic legal-AI competitor wouldn't think to build.

### 5. GI-Cluster Overlap Checker
Since GI protection is inherently geography-bound, add a lightweight module (even just a static lookup against the public GI registry) that warns a user proposing a GI-route product if a conflicting or overlapping GI already exists for that region/product category (e.g., someone claiming "Kashmir" origin for a product overlapping an existing registered GI). Cheap to build (it's a lookup, not a model), and closes a real gap — the roadmap currently tells people to pursue GI without checking if that specific GI claim is even viable.

### 6. Confidence-Weighted Human Escalation Network
Rather than escalation being a dead-end "contact a lawyer" message, position it as a **structured handoff** to a named partner network (AYUSH law clinics, IP cells at AYUSH TBIs) with the full Analysis object attached — so a human reviewer starts from the system's structured classification and citations instead of a blank consultation. This is a real workflow completion (matches the master-prompt's required USER PROBLEM → ... → ACTION → VERIFICATION → OUTCOME chain) rather than the system quietly giving up when confidence is low.

### 7. Multi-Formulation Comparator *(stretch — build only if core pipeline is solid with time to spare)*
Let a user compare two formulation variants side-by-side (e.g., "raw extract" vs. "98% standardized fraction") and see how the IP posture changes — directly demonstrates the value of *how* you formulate, not just *what*, which is the actual decision AYUSH R&D teams face. Genuinely valuable but adds real scope; treat as an if-time-permits polish item, not core-path.

### Recommended priority for a 36-hour build
Core pipeline (classify → retrieve → cite → roadmap) is non-negotiable and should consume the majority of the time. Of the additions above, **build #1 (Freshness Monitor) and #3 (Form pre-fill)** if any time remains — they're the two that most directly answer the strongest red-team attacks this idea has already faced ("the law will change under you" and "this is just a chatbot"), and both are cheap relative to their narrative payoff. Treat #2, #5, #6 as "here's our roadmap" slide content even if not fully built, and #7 as backlog.
