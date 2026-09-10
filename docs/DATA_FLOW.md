# IP-SAKTI — Data Flow & Sequence Diagrams

**Version:** 1.0  
**Last Updated:** September 2026

---

## 1. Analysis Creation Flow (Happy Path)

```
User          API           AnalysisService    Classifier   Retrieval    Synthesis   Verifier    DB
 │             │                  │                │             │            │           │        │
 │─POST /analyze►│                  │                │             │            │           │        │
 │             │──create Job──────────────────────────────────────────────────────────────────────►│
 │             │◄─202 Accepted──── │                │             │            │           │        │
 │             │                  │                │             │            │           │        │
 │             │            Worker polls            │             │            │           │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──classify()────►│             │            │           │        │
 │             │                  │◄─ClassificationResult─────── │             │            │           │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──retrieve()───────────────── ►│             │            │           │        │
 │             │                  │◄─StatutoryChunk[]──────────── │             │            │           │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──synthesize()──────────────────────────── ►│            │           │        │
 │             │                  │◄─RoadmapStep[]─────────────────────────── │             │            │           │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──verify()──────────────────────────────────────────── ►│        │
 │             │                  │◄─(passed=true, failed=[])────────────────────────────── │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──score_confidence()──────────────────────────────────── │        │
 │             │                  │                │             │            │           │        │
 │             │                  │──save Analysis(delivered)──────────────────────────────────────►│
 │             │                  │                │             │            │           │        │
 │─GET /analyses/{id}►│                  │                │             │            │           │        │
 │             │──fetch ────────────────────────────────────────────────────────────────────────►│
 │◄──Analysis (delivered, roadmap)──── │                │             │            │           │        │
```

---

## 2. Citation Failure & Retry Flow

```
                  Synthesis          Verifier         Synthesis (retry)     Verifier
                      │                 │                    │                  │
 ──synthesize()──────►│                 │                    │                  │
 ◄─RoadmapStep[]──── │                 │                    │                  │
                      │                 │                    │                  │
 ──verify()──────────────────────────► │                    │                  │
 ◄─(passed=false, failed=["Step 2:..."])│                    │                  │
                      │                 │                    │                  │
 ──synthesize(correction_prompt)──────────────────────────► │                  │
 ◄─RoadmapStep[]──────────────────────────────────────────── │                  │
                      │                 │                    │                  │
 ──verify()──────────────────────────────────────────────────────────────────► │
 ◄─(passed=true)──────────────────────────────────────────────────────────────── │
                      │                 │                    │                  │
 ──save(delivered)
```

---

## 3. Escalation Flow (All Paths)

```
AnalysisService                  EscalationService         Reviewer         User
      │                                  │                     │              │
      │ [Ambiguous classification]        │                     │              │
      │──or [confidence < 0.5]           │                     │              │
      │──or [citation failure × 2]       │                     │              │
      │                                  │                     │              │
      │──create EscalationRequest()─────►│                     │              │
      │──set analysis.status=escalated   │                     │              │
      │                                  │──notify_reviewer()──►│              │
      │                                  │                     │              │
      │                                  │                     │──review case─►│(dashboard)
      │                                  │                     │              │
      │                                  │◄─resolve(notes)──── │              │
      │                                  │──notify_user()──────────────────── ►│
      │                                  │                     │              │
      │                                  │──create new Analysis (optional)     │
```

---

## 4. Freshness Monitor Flow

```
FreshnessMonitor (nightly cron)        DB                    User
        │                               │                      │
        │──poll gazette sources         │                      │
        │◄─amendment detected           │                      │
        │                               │                      │
        │──INSERT statutory_amendments──►│                      │
        │                               │                      │
        │──UPDATE analyses              │                      │
        │  SET freshness_status='stale' │                      │
        │  WHERE analysis_id IN (       │                      │
        │    SELECT analysis_id FROM    │                      │
        │    analysis_citations         │                      │
        │    WHERE chunk_id = amended)──►│                      │
        │                               │                      │
        │──send_notification()──────────────────────────────── ►│
        │  "Law underlying your roadmap │                      │
        │   has changed. Re-analyse now"│                      │
        │                               │                      │
        │                               │     [User clicks re-analyse]
        │                               │◄─POST /reanalyze──── │
        │──new Analysis (supersedes old)►│                      │
```

---

## 5. Re-Analysis (Supersession) Flow

```
User             API              DB
  │               │                │
  │─POST /reanalyze►│               │
  │               │─fetch current Analysis (delivered)──►│
  │               │◄─analysis_v1                         │
  │               │                                      │
  │               │─create analysis_v2 (queued)──────────►│
  │               │─set analysis_v1.superseded_by = v2───►│
  │               │                                      │
  │◄─202 Accepted──│                                      │
  │               │                                      │
  │               │    [Worker runs pipeline on v2]       │
  │               │                                      │
  │               │─save analysis_v2 (delivered)──────────►│
  │               │─set analysis_v1.freshness_status =    │
  │               │  'superseded'─────────────────────────►│
```

---

## 6. Portfolio Batch Analysis Flow

```
IncubatorAdmin          API              Queue            Worker (×N)
       │                 │                 │                  │
       │─POST /portfolios/{id}/batch─────► │                  │
       │                 │─create N Jobs──►│                  │
       │◄─202 Accepted───│                 │                  │
       │                 │                 │                  │
       │                 │                 │──dispatch Job 1──►│
       │                 │                 │──dispatch Job 2──►│ (parallel)
       │                 │                 │──dispatch Job 3──►│
       │                 │                 │                  │
       │                 │                 │◄─done (Job 1)─── │
       │                 │                 │◄─done (Job 2)─── │
       │                 │                 │◄─done (Job 3)─── │
       │                 │                 │                  │
       │─GET /portfolios/{id}────────────► │                  │
       │◄─portfolio with all analyses──── │                  │
```

---

## 7. User Authentication Flow (Clerk)

```
Browser            Clerk (CDN)          IP-SAKTI API
   │                    │                    │
   │─login form─────────►│                   │
   │◄─JWT session token──│                   │
   │                    │                    │
   │─API request (with Bearer JWT)──────────►│
   │                    │                    │─verify JWT (Clerk public key)
   │                    │                    │◄─user_id, role
   │                    │                    │
   │                    │                    │─enforce RBAC
   │◄─response──────────────────────────────│
```

---

## 8. State Machine: Analysis Status

```
         ┌──────────────────────────────────────────────────┐
         │                                                  │
    [POST /analyze]                                         │
         │                                                  │
         ▼                                                  │
      queued ──Worker picks up──▶ processing                │
                                      │                     │
                              LLM synthesis starts          │
                                      │                     │
                                      ▼                     │
                                 synthesizing               │
                                      │                     │
                              Citation verifier runs        │
                                 ┌────┴────┐                │
                               pass      fail (retry 1)     │
                                 │            │             │
                                 │     [retry synthesis]    │
                                 │            │             │
                                 │        ┌─pass        fail (retry 2) ──▶ escalated
                                 │        │                               (reason: system_citation_failure)
                                 ▼        ▼
                             confidence scoring
                                 │
                    ┌────────────┴────────────┐
                 ≥ 0.5                      < 0.5
             not ambiguous               or ambiguous
                    │                        │
                    ▼                        ▼
                delivered                escalated
                    │
         [freshness_monitor detects change]
                    │
                    ▼
                  stale ──[user re-analyses]──▶ superseded
                                                    │
                                             new analysis
                                             starts at queued
```

---

## 9. Confidence Score Calculation (Data Flow)

```
citation_verifier.verify(steps, chunks)
        │
        ├── citation_pass_rate = steps_passed / total_steps
        │
retrieval output
        │
        ├── avg_retrieval_relevance = mean(chunk.relevance_score for chunk in chunks)
        │
classifier output
        │
        ├── classification_certainty = 0.0 if Ambiguous else 1.0
        │
        ▼
confidence = (0.5 × citation_pass_rate)
           + (0.3 × avg_retrieval_relevance)
           + (0.2 × classification_certainty)
        │
        ├── confidence < 0.5 → escalate(reason="low_confidence")
        ├── classification == "Ambiguous" → escalate(reason="ambiguous_classification")
        └── else → deliver
```
