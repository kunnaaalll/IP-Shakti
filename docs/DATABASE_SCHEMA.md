# IP-SAKTI — Database Schema

**Version:** 1.0  
**Database:** PostgreSQL 16 + pgvector extension  
**Last Updated:** September 2026

---

## 1. Setup

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## 2. Enum Types

```sql
CREATE TYPE classification_enum AS ENUM (
  'Classical',
  'Patent&Proprietary',
  'Phytopharmaceutical',
  'Aahar',
  'Ambiguous'
);

CREATE TYPE jurisdiction_enum AS ENUM (
  'IN',
  'INTL'
);

CREATE TYPE analysis_status_enum AS ENUM (
  'queued',
  'processing',
  'synthesizing',
  'delivered',
  'escalated'
);

CREATE TYPE formulation_status_enum AS ENUM (
  'draft',
  'analysing',
  'analysed',
  'escalated'
);

CREATE TYPE job_status_enum AS ENUM (
  'queued',
  'processing',
  'done',
  'failed'
);

CREATE TYPE escalation_reason_enum AS ENUM (
  'ambiguous_classification',
  'low_confidence',
  'system_citation_failure',
  'system_unavailable',
  'user_requested'
);

CREATE TYPE risk_level_enum AS ENUM (
  'low',
  'medium',
  'high',
  'blocker'
);

CREATE TYPE freshness_status_enum AS ENUM (
  'current',
  'stale',
  'superseded'
);

CREATE TYPE user_role_enum AS ENUM (
  'user',
  'reviewer',
  'incubator_admin',
  'system_admin'
);
```

---

## 3. Tables

### 3.1 `users`

Managed by Clerk; this table stores the IP-SAKTI-specific profile linked to the Clerk user ID.

```sql
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_user_id   TEXT NOT NULL UNIQUE,              -- Clerk's user identifier
  email           TEXT NOT NULL UNIQUE,
  full_name       TEXT,
  role            user_role_enum NOT NULL DEFAULT 'user',
  organisation    TEXT,                              -- incubator or company name
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at      TIMESTAMPTZ                        -- soft delete
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_role     ON users(role);
```

---

### 3.2 `formulations`

A single formulation submitted by a user. Status tracks its overall lifecycle.

```sql
CREATE TABLE formulations (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Core fields (editable only while status = 'draft')
  ingredients         TEXT[] NOT NULL,               -- array of ingredient names
  extraction_method   TEXT NOT NULL,
  intended_use        TEXT NOT NULL,
  claims_text         TEXT NOT NULL CHECK (char_length(claims_text) <= 3000),
  jurisdiction        jurisdiction_enum NOT NULL DEFAULT 'IN',

  -- Optional metadata
  product_name        TEXT,
  notes               TEXT,
  language            TEXT NOT NULL DEFAULT 'en',    -- source language of input

  -- Lifecycle
  status              formulation_status_enum NOT NULL DEFAULT 'draft',

  -- Timestamps
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at          TIMESTAMPTZ,                   -- soft delete; text fields purged on delete

  CONSTRAINT formulations_claims_length CHECK (char_length(claims_text) <= 3000),
  CONSTRAINT formulations_ingredients_count CHECK (array_length(ingredients, 1) <= 100)
);

CREATE INDEX idx_formulations_user_id ON formulations(user_id);
CREATE INDEX idx_formulations_status  ON formulations(status);
CREATE INDEX idx_formulations_created ON formulations(created_at DESC);
```

---

### 3.3 `analyses`

One analysis per formulation per jurisdiction. Immutable once delivered.

```sql
CREATE TABLE analyses (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  formulation_id          UUID NOT NULL REFERENCES formulations(id) ON DELETE CASCADE,

  -- Classification output (from the deterministic classifier)
  classification          classification_enum NOT NULL,
  classification_trace    TEXT[] NOT NULL DEFAULT '{}',  -- explainability trace
  tkrc_code               TEXT,                          -- e.g. 'TKRC-A61K-36/00-ASH'
  tkrc_name               TEXT,

  -- Pipeline metadata
  jurisdiction            jurisdiction_enum NOT NULL,
  confidence_score        NUMERIC(5,4),                  -- 0.0000 to 1.0000
  retries_used            SMALLINT NOT NULL DEFAULT 0,
  chunks_retrieved        SMALLINT NOT NULL DEFAULT 0,

  -- Lifecycle
  status                  analysis_status_enum NOT NULL DEFAULT 'queued',
  freshness_status        freshness_status_enum NOT NULL DEFAULT 'current',

  -- Versioning — immutability invariant
  supersedes_analysis_id  UUID REFERENCES analyses(id),  -- points to the analysis this replaces
  superseded_by_id        UUID REFERENCES analyses(id),  -- set when this is replaced

  -- Timestamps
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  delivered_at            TIMESTAMPTZ,                   -- set when status → delivered
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analyses_formulation_id ON analyses(formulation_id);
CREATE INDEX idx_analyses_status         ON analyses(status);
CREATE INDEX idx_analyses_freshness      ON analyses(freshness_status);
CREATE INDEX idx_analyses_classification ON analyses(classification);

-- Idempotency guard: block duplicate in-flight jobs for the same formulation+jurisdiction
CREATE UNIQUE INDEX idx_analyses_inflight
  ON analyses(formulation_id, jurisdiction)
  WHERE status IN ('queued', 'processing', 'synthesizing');
```

---

### 3.4 `roadmap_steps`

Each step in a delivered roadmap. Append-only; never edited after creation.

```sql
CREATE TABLE roadmap_steps (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id     UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  step_number     SMALLINT NOT NULL,                 -- 1-indexed ordering
  action          TEXT NOT NULL,
  rationale       TEXT NOT NULL,
  risk_level      risk_level_enum NOT NULL,
  timeline_note   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT roadmap_steps_unique_order UNIQUE (analysis_id, step_number)
);

CREATE INDEX idx_roadmap_steps_analysis_id ON roadmap_steps(analysis_id);
```

---

### 3.5 `statutory_chunks`

The statutory corpus. Each chunk is a discrete section of law, indexed for both
full-text and vector search.

```sql
CREATE TABLE statutory_chunks (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id        TEXT NOT NULL UNIQUE,              -- human-readable ID, e.g. 'PA-3P'
  act             TEXT NOT NULL,                     -- e.g. 'Patents Act, 1970'
  section         TEXT NOT NULL,                     -- e.g. '3(p)'
  text            TEXT NOT NULL,
  applies_to      classification_enum[] NOT NULL,    -- which classification buckets use this
  jurisdiction    jurisdiction_enum NOT NULL DEFAULT 'IN',

  -- Full-text search vector (updated by trigger)
  search_vector   TSVECTOR,

  -- Vector embedding for semantic search (384-dim MiniLM)
  embedding       VECTOR(384),

  -- Metadata
  effective_date  DATE,
  source_url      TEXT,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Full-text search index
CREATE INDEX idx_statutory_chunks_fts   ON statutory_chunks USING GIN(search_vector);

-- Vector similarity index (IVFFlat — suitable for ~5k chunks)
CREATE INDEX idx_statutory_chunks_vec   ON statutory_chunks USING ivfflat(embedding vector_cosine_ops)
  WITH (lists = 100);

-- Scope filtering index
CREATE INDEX idx_statutory_chunks_scope ON statutory_chunks USING GIN(applies_to);
CREATE INDEX idx_statutory_chunks_active ON statutory_chunks(is_active) WHERE is_active = TRUE;

-- Trigger to auto-update tsvector
CREATE OR REPLACE FUNCTION update_statutory_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := to_tsvector('english', NEW.act || ' ' || NEW.section || ' ' || NEW.text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER statutory_chunks_search_vector_update
  BEFORE INSERT OR UPDATE ON statutory_chunks
  FOR EACH ROW EXECUTE FUNCTION update_statutory_search_vector();
```

---

### 3.6 `analysis_citations`

Join table linking roadmap steps to the statutory chunks they cite.
This is the enforced evidence trail.

```sql
CREATE TABLE analysis_citations (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  roadmap_step_id   UUID NOT NULL REFERENCES roadmap_steps(id) ON DELETE CASCADE,
  chunk_id          TEXT NOT NULL REFERENCES statutory_chunks(chunk_id),
  -- Denormalised for fast display (avoids join on every roadmap render)
  act               TEXT NOT NULL,
  section           TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_citations_step_id  ON analysis_citations(roadmap_step_id);
CREATE INDEX idx_citations_chunk_id ON analysis_citations(chunk_id);
```

---

### 3.7 `escalation_requests`

One record per escalated analysis. Tracks the human review lifecycle.

```sql
CREATE TABLE escalation_requests (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id         UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  user_id             UUID NOT NULL REFERENCES users(id),
  assigned_reviewer   UUID REFERENCES users(id),          -- NULL until assigned

  reason              escalation_reason_enum NOT NULL,
  pipeline_trace      JSONB NOT NULL DEFAULT '{}',        -- full pipeline execution log
  failed_claims       TEXT[] NOT NULL DEFAULT '{}',       -- from citation_verifier

  -- Resolution
  resolved_at         TIMESTAMPTZ,
  resolution_notes    TEXT,

  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_escalations_analysis_id ON escalation_requests(analysis_id);
CREATE INDEX idx_escalations_reviewer    ON escalation_requests(assigned_reviewer);
CREATE INDEX idx_escalations_resolved    ON escalation_requests(resolved_at) WHERE resolved_at IS NULL;
```

---

### 3.8 `jobs`

Async job queue backed by Postgres. Workers poll this table.

```sql
CREATE TABLE jobs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  analysis_id     UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
  status          job_status_enum NOT NULL DEFAULT 'queued',
  attempt_count   SMALLINT NOT NULL DEFAULT 0,
  last_error      TEXT,
  scheduled_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_status       ON jobs(status, scheduled_at) WHERE status = 'queued';
CREATE INDEX idx_jobs_analysis_id  ON jobs(analysis_id);
```

---

### 3.9 `portfolios`

A named collection of formulations, used by incubators to track cohorts.

```sql
CREATE TABLE portfolios (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  description     TEXT,
  is_public       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_portfolios_owner_id ON portfolios(owner_id);
```

---

### 3.10 `portfolio_formulations`

Join table for the Portfolio ↔ Formulation many-to-many relationship.

```sql
CREATE TABLE portfolio_formulations (
  portfolio_id    UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  formulation_id  UUID NOT NULL REFERENCES formulations(id) ON DELETE CASCADE,
  added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  notes           TEXT,

  PRIMARY KEY (portfolio_id, formulation_id)
);

CREATE INDEX idx_pf_portfolio_id    ON portfolio_formulations(portfolio_id);
CREATE INDEX idx_pf_formulation_id  ON portfolio_formulations(formulation_id);
```

---

### 3.11 `statutory_amendments`

Tracks changes to the statutory corpus, used by the Freshness Monitor.

```sql
CREATE TABLE statutory_amendments (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chunk_id        TEXT NOT NULL REFERENCES statutory_chunks(chunk_id),
  amendment_type  TEXT NOT NULL CHECK (amendment_type IN ('update', 'repeal', 'insert')),
  description     TEXT NOT NULL,
  gazette_ref     TEXT,                              -- gazette notification reference
  effective_date  DATE NOT NULL,
  detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed       BOOLEAN NOT NULL DEFAULT FALSE     -- TRUE once affected analyses are flagged
);

CREATE INDEX idx_amendments_chunk_id   ON statutory_amendments(chunk_id);
CREATE INDEX idx_amendments_processed  ON statutory_amendments(processed) WHERE processed = FALSE;
```

---

## 4. Entity Relationship Diagram

```
users ──────────────────────────────────┐
  │                                     │
  ├──▶ formulations ──────────────────┐ │
  │       │                           │ │
  │       ├──▶ analyses               │ │
  │       │       │                   │ │
  │       │       ├──▶ roadmap_steps ─┼─┼──▶ analysis_citations ──▶ statutory_chunks
  │       │       │                   │ │
  │       │       ├──▶ escalation_requests (assigned_reviewer → users)
  │       │       │
  │       │       └──▶ jobs
  │       │
  │       └──▶ portfolio_formulations ──▶ portfolios (owner → users)
  │
  └── (reviewer) ──▶ escalation_requests.assigned_reviewer

statutory_chunks ◀──── statutory_amendments
```

---

## 5. Key Constraints Summary

| Constraint | Table | Rule |
|---|---|---|
| Claims text length | `formulations` | `≤ 3,000 characters` |
| Ingredient count | `formulations` | `≤ 100 items` |
| In-flight idempotency | `analyses` | Unique `(formulation_id, jurisdiction)` where status is active |
| Step ordering | `roadmap_steps` | Unique `(analysis_id, step_number)` |
| Citation integrity | `analysis_citations` | `chunk_id` must reference a real `statutory_chunks` row |
| Soft delete | `users`, `formulations` | `deleted_at` timestamp; text content purged on formulation delete |

---

## 6. Migration Strategy

Migrations are managed with a tool like **Flyway** or **golang-migrate**.

```
migrations/
├── V1__initial_schema.sql        ← extensions + enums + all tables
├── V2__add_multilingual.sql      ← add language column to formulations
├── V3__portfolio_mode.sql        ← portfolios + portfolio_formulations
└── V4__freshness_monitor.sql     ← statutory_amendments + freshness_status enum
```

**Rules:**
- Migrations are append-only. Never edit a committed migration file.
- Every migration must be tested against a production snapshot before deploying.
- Destructive changes (column drops) require a two-phase migration:
  1. Deploy code that doesn't use the column
  2. Drop the column in a subsequent migration

---

## 7. Sample Queries

### Fetch a delivered analysis with its full roadmap and citations

```sql
SELECT
  a.id,
  a.classification,
  a.confidence_score,
  a.status,
  rs.step_number,
  rs.action,
  rs.rationale,
  rs.risk_level,
  rs.timeline_note,
  json_agg(json_build_object(
    'act', ac.act,
    'section', ac.section,
    'chunk_id', ac.chunk_id
  )) AS citations
FROM analyses a
JOIN roadmap_steps rs ON rs.analysis_id = a.id
JOIN analysis_citations ac ON ac.roadmap_step_id = rs.id
WHERE a.id = $1
  AND a.status = 'delivered'
GROUP BY a.id, rs.id
ORDER BY rs.step_number;
```

### Hybrid retrieval — keyword + vector ranked by weighted score

```sql
SELECT
  sc.chunk_id,
  sc.act,
  sc.section,
  sc.text,
  ts_rank(sc.search_vector, query) AS keyword_score,
  1 - (sc.embedding <=> $embedding) AS vector_score,
  (0.5 * ts_rank(sc.search_vector, query) +
   0.5 * (1 - (sc.embedding <=> $embedding))) AS hybrid_score
FROM statutory_chunks sc,
     to_tsquery('english', $query_text) AS query
WHERE sc.is_active = TRUE
  AND $classification = ANY(sc.applies_to)
  AND sc.jurisdiction = $jurisdiction
  AND (
    sc.search_vector @@ query
    OR (sc.embedding <=> $embedding) < 0.5
  )
ORDER BY hybrid_score DESC
LIMIT 5;
```

### Flag analyses as stale after a statutory amendment

```sql
UPDATE analyses
SET freshness_status = 'stale', updated_at = NOW()
WHERE id IN (
  SELECT DISTINCT rs.analysis_id
  FROM analysis_citations ac
  JOIN roadmap_steps rs ON rs.id = ac.roadmap_step_id
  WHERE ac.chunk_id = $amended_chunk_id
)
AND status = 'delivered'
AND freshness_status = 'current';
```
