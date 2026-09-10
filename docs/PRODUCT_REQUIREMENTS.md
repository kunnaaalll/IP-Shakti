# IP-SAKTI — Product Requirements Document

**Version:** 1.0  
**Last Updated:** September 2026  
**Problem Statement:** SIH26045

---

## 1. Problem Statement

India's AYUSH sector produces thousands of new formulations annually. Individual formulators,
student innovators, and small manufacturers have no affordable, fast, reliable way to answer
a basic pre-investment question:

> **"Can I patent this formulation — and if not, what can I actually do to protect it?"**

The barriers today:
1. **Access** — The only reliable answer requires a patent attorney specialising in AYUSH IP
2. **Cost** — Initial consultations cost ₹15,000–₹50,000
3. **Time** — Multi-week turnaround before any clarity
4. **Complexity** — A single formulation touches Patents Act, Biological Diversity Act, Drugs &
   Cosmetics Act, FSSAI, and GI Act simultaneously
5. **TKDL wall** — The authoritative prior-art tool (TKDL) is NDA-gated to patent offices;
   no public tool can access it at any price

The people most harmed are exactly who the AYUSH startup ecosystem depends on: first-time
innovators and small manufacturers who cannot absorb a multi-thousand-rupee consultation
just to discover their idea is already unpatentable.

---

## 2. Solution

IP-SAKTI is a decision-support system that:
- Takes a formulation description in natural language (English or Hindi)
- Returns a citation-verified IP strategy roadmap in minutes, for free
- Never shows a legal claim it cannot prove against a retrieved section of law
- Admits when it genuinely cannot classify, instead of guessing

It is explicitly **not** a filing agent and does not replace legal counsel. It replaces
the first screening step that currently costs founders weeks and money.

---

## 3. Target Users

### Primary: Individual AYUSH Formulator / Student Innovator

**Profile:** First-time innovator, AYUSH degree student, Ayurvedic doctor with a novel
formulation idea. Has no legal background and no budget for a patent attorney.

**Job to be done:** Understand whether my formulation is patentable before spending money
on filing, and if not, what alternatives exist.

**Success looks like:** Gets a clear, actionable answer in < 5 minutes with citations they
can show to an attorney if they proceed further.

---

### Secondary: Small AYUSH Manufacturer

**Profile:** Running a manufacturing unit with 2–20 formulations in development. Needs to
screen ideas quickly before investing in R&D.

**Job to be done:** Screen multiple product ideas for IP viability in a single session.

**Success looks like:** Can run 5–10 formulations through the tool in an afternoon and
prioritise which ones warrant a formal attorney consultation.

---

### Secondary: AYUSH Incubator / TBI Staff

**Profile:** Manages 20–100 startup applicants per cohort. Currently screens IP informally
or defers to expensive expert panels.

**Job to be done:** Screen entire applicant portfolios for basic IP viability at cohort scale.

**Success looks like:** Portfolio Mode surfaces a classification and confidence score for
every applicant's formulation within 24 hours of submission.

---

### Tertiary: Patent Agent

**Profile:** Registered patent agent handling AYUSH clients. Wants a fast first-draft
classification and relevant statutory sections before a detailed consultation.

**Job to be done:** Get a structured starting point that saves 1–2 hours of initial research.

---

### Explicit Non-Users

- **Patent examiners** — have TKDL access; IP-SAKTI adds no value
- **Large pharma** — have in-house counsel; not the target
- **Anyone seeking to bypass the IP system** — IP-SAKTI is a compliance aid, not a workaround

---

## 4. User Stories

### Core Pipeline

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-01 | As a formulator, I can submit my formulation in plain English so that I get an IP analysis without legal expertise | Form accepts free-text ingredients, method, use, and claims; submits successfully |
| US-02 | As a formulator, I can see my formulation classified into an IP bucket so that I understand its legal category | Classification is shown with a human-readable explanation trace |
| US-03 | As a formulator, I can see which specific statutory sections apply to my formulation so that I know the exact legal basis | Every roadmap step shows the Act, Section, and text of the cited chunk |
| US-04 | As a formulator, I can see a step-by-step IP roadmap so that I know what actions to take | Roadmap has ≥1 step, each with action, rationale, risk level, and citations |
| US-05 | As a formulator, I can see a confidence score so that I know how certain the system is | Confidence score (0.0–1.0) is displayed with a plain-language interpretation |
| US-06 | As a formulator, I want the system to admit it doesn't know rather than give me a wrong answer | Ambiguous formulations show Ambiguous classification and route to human review |
| US-07 | As a formulator, I can download my analysis as a PDF so that I can share it | PDF export contains the full roadmap with citations and disclaimer |

---

### Citation Integrity

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-08 | As a formulator, I need to trust that every legal statement in my roadmap is backed by law | Zero unverified claims reach the delivered state |
| US-09 | As a formulator, I want the system to retry if it makes an error rather than showing me the error | Synthesis retries automatically on citation failure; user sees no retry artifact |
| US-10 | As a formulator, I want to be connected to a human expert when the system is uncertain | Escalation creates an EscalationRequest and notifies the reviewer network within 5 minutes |

---

### Freshness & Versioning

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-11 | As a formulator, I want to know if the law underlying my analysis has changed | Stale analyses show a banner with a one-click re-analyse button |
| US-12 | As a formulator, I can re-analyse my formulation after a law change without losing my old analysis | Re-analysis creates a new Analysis; old one is preserved with superseded status |

---

### Portfolio Mode

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-13 | As an incubator admin, I can create a portfolio and add applicant formulations so that I manage cohort screening centrally | Portfolio CRUD; add/remove formulations; view classification summary for all |
| US-14 | As an incubator admin, I can batch-submit a portfolio for analysis so that I don't have to trigger each one manually | Batch endpoint triggers analyses for all unanalysed formulations in a portfolio |
| US-15 | As an incubator admin, I can see a summary dashboard for my portfolio so that I can quickly identify which formulations need attention | Dashboard shows classification, confidence, and freshness for each formulation |

---

### Escalation Review

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-16 | As a reviewer, I can see the full pipeline trace for escalated analyses so that I understand why the system couldn't deliver | Pipeline trace, retrieved chunks, failed claims, and confidence score are all shown |
| US-17 | As a reviewer, I can post resolution notes on an escalation so that the user gets a human-validated answer | Resolution form; user receives notification when resolved |

---

### Statute Search

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-18 | As any user (including unauthenticated), I can search the statutory corpus so that I can read the source law | Search returns matching chunks with act, section, and full text; no auth required |
| US-19 | As any developer, I can subscribe to the statutory changes feed so that my downstream tool stays current | `/statutes/changes?since=DATE` returns amendments in a stable JSON format |

---

## 5. Classification Specification

| Bucket | Definition | Key Statute |
|---|---|---|
| **Classical** | Formulation matches a documented classical Ayurveda / Siddha / Unani text AND uses traditional processing methods | Patents Act §3(p) — barred from standard patent; eligible for GI, trademark |
| **Patent & Proprietary** | Novel process, synthetic carrier, chemically modified extraction, or new molecule not found in classical texts | Patents Act §2(1)(j) — must demonstrate inventive step; §3(d) — efficacy bar for known substances |
| **Phytopharmaceutical** | Purified / standardised extract with ≥4 defined bioactive compounds | AYUSH Phytopharmaceutical Drugs Notification, 2015 — separate regulatory pathway |
| **Aahar** | Positioned as a food, nutraceutical, dietary supplement, or health drink | FSSAI / Food Safety and Standards Act §22 — not a drug; different approval path |
| **Ambiguous** | Does not cleanly fit any bucket | Routes to human review — this is a valid, designed terminal state |

---

## 6. Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Analysis latency (rule-based)** | < 5 seconds end-to-end |
| **Analysis latency (LLM mode)** | < 45 seconds end-to-end |
| **API availability** | 99.5% uptime |
| **Concurrent analyses** | 20 simultaneous without degradation |
| **Statute search response time** | < 500ms p95 |
| **PDF export generation** | < 3 seconds |
| **Escalation notification** | < 5 minutes after escalation |
| **Freshness Monitor** | Detects amendments within 24 hours of gazette publication |
| **Mobile responsiveness** | Full functionality on screens ≥ 375px wide |
| **Language support** | English (primary); Hindi (Bhashini integration) |

---

## 7. Out of Scope (v1)

| Feature | Reason |
|---|---|
| TKDL search | NDA-gated by international agreement; cannot be integrated at any price |
| IP filing | Not a filing agent; explicitly outside the product boundary |
| Legal advice | Every output carries "informational only" disclaimer |
| Court document generation | Out of scope; downstream of this tool |
| Trademark / GI filing | Out of scope; referenced in roadmap but not filed |
| Full Indian statutory corpus | v1 targets the 8–10 most critical sections for AYUSH IP |
| Real-time gazette monitoring | v1 uses nightly batch; real-time is a v2 enhancement |

---

## 8. Success Metrics

| Metric | Definition | Target (3 months post-launch) |
|---|---|---|
| **Analyses delivered** | Count of analyses reaching `delivered` status | 500/month |
| **Citation pass rate** | % of analyses delivered without a retry | > 85% |
| **Escalation rate** | % of analyses routed to human review | < 20% |
| **User return rate** | % of users who submit ≥2 formulations | > 40% |
| **Portfolio adoption** | Count of active portfolios | 5 incubators |
| **Time to first analysis** | Time from account creation to first delivered analysis | < 10 minutes |
| **Confidence score distribution** | Average confidence across delivered analyses | > 0.70 |
| **Freshness coverage** | % of statutory chunks with a last-verified date < 90 days | 100% |

---

## 9. Constraints

- **TKDL inaccessibility:** The product must work without TKDL. The TKRC (Traditional
  Knowledge Resource Classification) public scheme is used as a directional signal instead.
- **Legal liability:** IP-SAKTI is not a law firm. All outputs carry an
  "informational only — not legal advice" disclaimer with a clear escalation path to human reviewers.
- **Corpus coverage:** v1 targets the minimum viable statutory corpus needed for AYUSH IP
  triage. Gaps in coverage must result in escalation, not hallucinated guidance.
- **Language:** English is the primary interface language in v1. Hindi support via Bhashini
  is planned but depends on Bhashini API stability.
