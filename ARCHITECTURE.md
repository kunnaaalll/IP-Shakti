# IP-SAKTI — Architecture Reference

Condensed technical reference for the full-scale system design. The prototype in
`/prototype` implements a scoped-down version of the pipeline described here —
see `prototype/README.md` for what's simulated vs. real.

## Domain model

**Entities:** `User → Formulation → Analysis → AnalysisCitation → StatutoryChunk`,
plus `Portfolio`, `PortfolioFormulation` (join table), and `EscalationRequest`.

**Classification enum:** `Classical | Patent&Proprietary | Phytopharmaceutical |
Aahar | Ambiguous` — Ambiguous is a valid terminal state, not an error.

**Analysis status:** `queued → processing → synthesizing → delivered | escalated`

**Invariants:**
1. Every `RoadmapStep` must reference at least one `StatutoryChunk` — no
   un-cited recommendation is ever returned.
2. Classification is deterministic given the same inputs — owned by a decision
   tree, not the LLM.
3. An `Analysis` is immutable once delivered; law changes produce a new,
   superseding Analysis rather than an edit.
4. `Jurisdiction = International` analyses always include the India-domestic
   layer; international guidance is additive, never a replacement.

## Citation protocol

1. LLM emits a structured `citations` array (`{act, section, chunk_id}`)
   alongside the roadmap text — the model cites structured fields, not free text.
2. Verifier matches each `(act, section)` tuple against the chunks actually
   retrieved for that query — a field match against known-good IDs, not fuzzy
   string matching.
3. A secondary pattern scan flags legal-assertion language ("under Section",
   "pursuant to", "as per Rule") with no corresponding citation entry, catching
   paraphrased uncited claims.
4. Any failure → one retry with an explicit correction prompt listing exactly
   which claims failed. Second failure → escalate
   (`reason = system_citation_failure`), never shown to the user unverified.

## Confidence score

```
confidence = 0.5 × citation_pass_rate        (fraction verified on first pass)
           + 0.3 × avg_retrieval_relevance   (mean relevance of retrieved chunks)
           + 0.2 × classification_certainty  (1.0 clean terminal, 0.0 if Ambiguous)
```

Threshold: `confidence < 0.5` → auto-escalate (`reason = low_confidence`), even
if citation verification technically passed.

## API surface (core endpoints)

```
POST   /api/v1/formulations                     create (draft)
POST   /api/v1/formulations/{id}/analyze         202, async — kicks off pipeline
POST   /api/v1/formulations/{id}/reanalyze       new Analysis, supersedes old
PATCH  /api/v1/formulations/{id}                 edit while status=draft only
DELETE /api/v1/formulations/{id}                 soft delete, text purged
GET    /api/v1/analyses/{id}                     full analysis + roadmap
GET    /api/v1/analyses/{id}/export.pdf
POST   /api/v1/escalations
GET    /api/v1/statutes/search?q=...             public, unauthenticated
GET    /api/v1/statutes/changes?since=DATE       Freshness Monitor feed
POST   /api/v1/portfolios
GET    /api/v1/gi/overlap?region=...&product=...
```

All public-facing IDs are UUIDv4 (never sequential integers) to close IDOR by
construction. Role model: `user | reviewer | incubator_admin | system_admin`.

## Tech stack (full-scale target)

| Component | Choice | Why |
|---|---|---|
| Datastore | Postgres | Relational integrity for the Formulation→Analysis→Citation chain, `jsonb` for flexible fields |
| Vector index | pgvector | Corpus is a few thousand chunks — a separate vector DB is premature infra |
| Keyword search | Postgres `tsvector` | Same reasoning — one datastore |
| LLM provider | Provider-agnostic wrapper (LiteLLM) | No vendor lock-in for a legal-accuracy-critical system |
| Job queue | Postgres-backed table + polling worker | Dozens of concurrent jobs doesn't justify Kafka/RabbitMQ |
| Auth | Managed provider (Clerk/Supabase) | No unique value in building this from scratch |
| Frontend | Next.js + Tailwind | Judge-facing polish |
| PDF export | `@react-pdf/renderer` (client-side) | Shares component logic with the on-screen view |
| Translation | Bhashini | Government-backed, public digital infrastructure |

## Failure handling

- LLM provider down/timeout → 3 retries with exponential backoff, then
  `status = escalated`, `reason = system_unavailable` — never a dead end.
- Idempotency lives on the **job table**, not the Analysis table:
  `UNIQUE (formulation_id, jurisdiction) WHERE status IN ('queued','processing')`
  — blocks duplicate in-flight jobs without blocking legitimate re-analysis.
- Prompt injection: user content wrapped in `<formulation>...</formulation>`
  delimiters; system prompt states content inside is data, never instructions.
  Input caps: `claims_text` ≤ 3,000 chars, `ingredients` ≤ 100 items × 200 chars.

## Architecture pattern

Modular monolith — one deployable, one datastore, one linear request pipeline.
Module boundaries are by code, not network:

```
API Layer → Service Layer → Domain Modules (classifier / retrieval / synthesis /
citation_verifier / escalation) → Repository Layer → Postgres + pgvector
```

`citation_verifier/` is kept as its own mandatory module deliberately — inlining
it into `synthesis/` would make it easy to accidentally skip under time
pressure. No separate microservice for `escalation/` — it's simple enough to be
a service-layer concern.
