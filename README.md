# IP-SAKTI — Ayurveda IP Navigator

**SIH26045** — a decision-support tool that takes an Ayurveda formulation
description and returns a citation-verified IP strategy roadmap: what's
patentable, what's barred, what approvals are needed, and what alternative
protection routes exist.

## Contents

| File | What it is |
|---|---|
| `WHITEPAPER.md` | The project pitch — problem, solution, and why this isn't "just RAG" |
| `ARCHITECTURE.md` | Condensed technical reference for the full-scale system design |
| `prototype/` | A runnable proof-of-concept of the core verification pipeline |

## What the prototype proves

Not the full product — a **proof of concept** for the one idea the whole project
stands on: *a legal-answer pipeline that refuses to show a claim it can't prove.*

It implements, against a small hand-curated statutory corpus:

- deterministic classification (pure logic, no LLM)
- scoped hybrid retrieval (keyword + naive vector similarity)
- LLM-drafted roadmap synthesis, grounded only in retrieved chunks
- a hard citation-verification gate with reject-and-retry
- the confidence-scoring formula and escalation threshold
- the `Ambiguous` terminal state

See `prototype/README.md` to run it.

## Not in the prototype (by design)

Auth, Postgres, the full statutory corpus, PDF export, Freshness Monitor,
Portfolio Mode, and the Next.js frontend are all real-system concerns described
in `ARCHITECTURE.md` but deliberately out of scope for a proof of concept — the
prototype exists to validate the verification logic, not to be a deployable
product.

## Team

Built for Smart India Hackathon 2026, problem statement SIH26045.
