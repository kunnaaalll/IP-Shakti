<div align="center">

# IP-SAKTI
### Ayurveda IP Navigator

**Smart India Hackathon 2026 · Problem Statement SIH26045**

A decision-support system that produces **citation-verified IP strategy roadmaps**  
for Ayurveda formulations — what's patentable, what's barred, and what to do instead.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com)
[![SIH 2026](https://img.shields.io/badge/SIH-26045-orange.svg)](https://sih.gov.in)

</div>

---

## The Problem

India's AYUSH sector produces thousands of new formulations every year. A first-time formulator trying to understand their IP position faces a wall:

- A single formulation can touch **4 different Acts** simultaneously — Patents Act §3(p), Biological Diversity Act, Drugs & Cosmetics Act, and the GI Act
- The only reliable answer requires a **patent attorney specialising in AYUSH IP** — scarce, expensive, and slow
- The **TKDL** (the definitive prior-art tool for this domain) is NDA-gated to patent offices by international agreement — no public tool can access it

**Result:** First-time innovators spend weeks and thousands of rupees just to discover their idea was already unpatentable.

---

## What IP-SAKTI Does

Given a formulation description (ingredients, extraction method, intended use, claims), IP-SAKTI returns:

1. **A deterministic classification** — `Classical | Patent & Proprietary | Phytopharmaceutical | Aahar | Ambiguous`
2. **The specific statutory sections** that apply, retrieved and cited by source
3. **A step-by-step IP roadmap** — what's barred, what's viable, what approvals are needed
4. **A confidence score** — and honest escalation to a human reviewer when it isn't sure

> **Core principle:** No legal claim is ever shown to a user unless it can be traced to a specific, retrieved section of law.

---

## Why This Is Not "Just RAG"

| What RAG does | What IP-SAKTI does |
|---|---|
| Retrieves text, asks LLM to answer | LLM never touches classification — it's pure deterministic logic |
| Citations are courtesy references | Citations are a **hard gate** — unverified claims are rejected and retried |
| Hallucination is possible | Hallucinated `chunk_id` → verifier rejects → user never sees it |
| Uncertain answers are still given | `Ambiguous` is a designed terminal state — system admits it doesn't know |
| Answers are disposable | Analyses are immutable; law changes produce a new superseding version |

---

## Repository Structure

```
IP-Shakti/
├── README.md                        ← you are here
├── .gitignore
│
├── docs/                            ← full system documentation
│   ├── SYSTEM_DESIGN.md             ← architecture, modules, tech stack
│   ├── LLM_DESIGN.md                ← LLM strategy, prompts, provider routing
│   ├── DATABASE_SCHEMA.md           ← full Postgres DDL + pgvector setup
│   ├── API_REFERENCE.md             ← all endpoints with request/response schemas
│   ├── DATA_FLOW.md                 ← sequence diagrams for every major flow
│   ├── SECURITY.md                  ← auth, RBAC, prompt injection defence
│   ├── DEPLOYMENT.md                ← env vars, CI/CD, production checklist
│   ├── PRODUCT_REQUIREMENTS.md      ← personas, user stories, success metrics
│   ├── ARCHITECTURE.md              ← condensed technical reference
│   └── WHITEPAPER.md                ← project pitch document
│
└── prototype/                       ← runnable proof of concept
    ├── README.md                    ← how to run
    ├── main.py                      ← CLI entry point
    ├── app.py                       ← web server (Flask + SSE)
    ├── requirements.txt
    ├── data/
    │   ├── corpus.json              ← curated statutory chunks
    │   └── classical_texts.json     ← classical formulation lookup
    ├── ip_sakti/                    ← core pipeline package
    │   ├── classifier.py            ← deterministic decision tree (no LLM)
    │   ├── retrieval.py             ← scoped hybrid retrieval
    │   ├── synthesis.py             ← rule-based + LLM roadmap drafting
    │   ├── citation_verifier.py     ← hard gate + confidence formula
    │   └── models.py                ← typed dataclasses
    └── templates/
        └── index.html               ← dark-mode web UI
```

---

## Quick Start

**Web UI** (recommended — shows the live pipeline animation):

```bash
git clone https://github.com/kunnaaalll/IP-Shakti.git
cd IP-Shakti/prototype
pip install flask
python3 app.py
# open http://localhost:5000
```

**CLI** (no dependencies — pure Python stdlib):

```bash
cd IP-Shakti/prototype
python3 main.py --demo classical          # clean classical formulation
python3 main.py --demo ambiguous          # system honestly says "I don't know"
python3 main.py --demo bad-citation       # watch Stage 4 catch a hallucinated cite
```

---

## Pipeline at a Glance

```
Formulation Input
       │
       ▼
  Stage 1 — Deterministic Classification    (pure logic · zero LLM)
       │
       ▼
  Stage 2 — Scoped Hybrid Retrieval         (keyword + vector · Postgres pgvector)
       │
       ▼
  Stage 3 — Roadmap Synthesis               (rule-based default · optional LLM via LiteLLM)
       │
       ▼
  Stage 4 — Citation Verifier Gate          (hard gate · reject + retry · pure logic)
       │
       ▼
  Stage 5 — Confidence Scoring              (weighted formula · auto-escalate < 0.5)
       │
  ┌────┴────┐
  ▼         ▼
DELIVERED  ESCALATED → Human reviewer
```

---

## Demo Scenarios

| Scenario | Command | What it demonstrates |
|---|---|---|
| Classical formulation | `--demo classical` | §3(p) bar correctly applied; GI route suggested; TKRC match printed |
| Phytopharmaceutical | `--demo phytopharma` | Phyto notification pathway identified |
| Aahar / Nutraceutical | `--demo aahar` | FSSAI pathway surfaced instead of patent route |
| Patent & Proprietary | `--demo patent_proprietary` | Novel process → full patent eligibility analysis |
| Ambiguous | `--demo ambiguous` | System refuses to guess; routes to human review |
| **Hallucination catch** | `--demo bad-citation` | Stage 4 rejects a fabricated citation before the user sees it |

---

## Full-Scale Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Backend | Next.js API routes + Python analysis worker |
| Database | PostgreSQL 16 + pgvector |
| LLM | LiteLLM router → Anthropic Claude / Gemini / GPT-4o |
| Auth | Clerk |
| Translation | Bhashini API (22 scheduled languages) |
| PDF export | `@react-pdf/renderer` |
| Hosting | Vercel + Neon (serverless Postgres) |

> The prototype uses only Python stdlib + Flask. The `ip_sakti/` module boundaries mirror
> the full-scale architecture — moving to the production stack is adding persistence and
> API routes around the same logic, not rewriting it.

---

## Documentation

| Document | Description |
|---|---|
| [System Design](docs/SYSTEM_DESIGN.md) | Architecture pattern, all modules, tech stack rationale, failure handling |
| [LLM Design](docs/LLM_DESIGN.md) | Provider strategy, prompts, injection defence, evaluation |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Full Postgres DDL, 11 tables, pgvector setup |
| [API Reference](docs/API_REFERENCE.md) | All endpoints with request/response schemas |
| [Data Flow](docs/DATA_FLOW.md) | Sequence diagrams for every pipeline flow |
| [Security](docs/SECURITY.md) | Auth, RBAC, prompt injection, audit trail |
| [Deployment](docs/DEPLOYMENT.md) | CI/CD, Vercel, Neon, production checklist |
| [Product Requirements](docs/PRODUCT_REQUIREMENTS.md) | Personas, user stories, success metrics |
| [Whitepaper](docs/WHITEPAPER.md) | Project pitch — problem, solution, and impact |

---

## Team

Built for **Smart India Hackathon 2026**, problem statement **SIH26045**.

---

<div align="center">

*IP-SAKTI is informational only — not legal advice.*  
*For formal IP proceedings, consult a registered patent agent.*

</div>
