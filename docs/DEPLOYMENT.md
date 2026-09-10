# IP-SAKTI — Deployment Guide

**Version:** 1.0  
**Last Updated:** September 2026

---

## 1. Architecture Overview

```
                    ┌─────────────────────────────────┐
Internet ──HTTPS──► │        Vercel Edge Network       │
                    │   (Next.js frontend + API routes)│
                    └─────────────────┬───────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                    ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
                    │  Clerk  │ │  Neon   │ │ LiteLLM │
                    │  (Auth) │ │(Postgres│ │(LLM API │
                    │         │ │+pgvector│ │ Router) │
                    └─────────┘ └────▼────┘ └─────────┘
                                      │
                              ┌───────▼───────┐
                              │ Analysis Worker│
                              │ (long-running  │
                              │  Python/Node)  │
                              └───────────────┘
```

---

## 2. Environment Variables

Copy `.env.example` to `.env.local` for local development.
In production, these are set as Vercel encrypted environment variables.

```bash
# ── Database ──────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://user:password@host:5432/ipsakti?sslmode=require

# ── Auth (Clerk) ───────────────────────────────────────────────────────────
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# ── LLM Providers (via LiteLLM) ────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...

# ── Translation ────────────────────────────────────────────────────────────
BHASHINI_API_KEY=...
BHASHINI_USER_ID=...

# ── Email ──────────────────────────────────────────────────────────────────
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@ipsakti.in

# ── Application ────────────────────────────────────────────────────────────
NEXT_PUBLIC_APP_URL=https://ipsakti.in
NODE_ENV=production

# ── Worker (analysis pipeline) ─────────────────────────────────────────────
WORKER_POLL_INTERVAL_MS=2000          # how often the worker polls for queued jobs
WORKER_MAX_CONCURRENT_JOBS=5          # max parallel analyses per worker instance
LLM_MAX_RETRIES=3                     # LLM provider retry count
LLM_RETRY_DELAY_MS=1000               # base delay for exponential backoff
SYNTHESIS_MAX_RETRIES=1               # citation verification retry count
CONFIDENCE_THRESHOLD=0.5              # below this → auto-escalate

# ── Monitoring ─────────────────────────────────────────────────────────────
SENTRY_DSN=https://...@sentry.io/...
```

---

## 3. Local Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16 with pgvector extension
- A Clerk account (free tier is sufficient)

### Step 1 — Clone and install

```bash
git clone https://github.com/kunnaaalll/IP-Shakti.git
cd IP-Shakti
```

For the web frontend + API:
```bash
cd app                 # (when the full Next.js app exists)
npm install
```

For the prototype only:
```bash
cd prototype
pip install flask      # only dependency for the web UI
python3 app.py         # starts at http://localhost:5000
```

### Step 2 — Database setup

```bash
# Create database
createdb ipsakti

# Install pgvector
psql ipsakti -c "CREATE EXTENSION vector;"
psql ipsakti -c "CREATE EXTENSION \"uuid-ossp\";"

# Run migrations
psql ipsakti < migrations/V1__initial_schema.sql
psql ipsakti < migrations/V2__seed_corpus.sql
```

### Step 3 — Seed the statutory corpus

```bash
python3 scripts/seed_corpus.py --db $DATABASE_URL --corpus data/corpus.json
python3 scripts/embed_corpus.py --db $DATABASE_URL  # computes pgvector embeddings
```

### Step 4 — Run locally

```bash
# Terminal 1 — Next.js dev server
npm run dev

# Terminal 2 — Analysis worker
python3 worker/main.py
```

---

## 4. Database Provisioning (Neon)

[Neon](https://neon.tech) is the recommended serverless Postgres provider — it supports
pgvector natively and scales to zero between demos.

```bash
# Install Neon CLI
npm install -g neonctl

# Create project
neonctl projects create --name ipsakti

# Get connection string
neonctl connection-string --project-id <id>

# Enable pgvector
neonctl sql "CREATE EXTENSION vector;" --project-id <id>
```

**Branching strategy with Neon:**

```
main branch      ← production database
  └── dev branch ← development (auto-branched from main)
       └── pr/123 ← per-PR ephemeral branch (dropped after merge)
```

This gives each PR its own isolated database state at zero cost.

---

## 5. Vercel Deployment

### Initial setup

```bash
npm install -g vercel
vercel login
vercel link   # link to the Vercel project
```

### Deploy to production

```bash
vercel --prod
```

### Environment variables

Set via the Vercel dashboard (Settings → Environment Variables) or CLI:

```bash
vercel env add ANTHROPIC_API_KEY production
vercel env add DATABASE_URL production
vercel env add CLERK_SECRET_KEY production
# ... etc for all variables in Section 2
```

### Vercel project settings

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["bom1"]
}
```

`bom1` is Vercel's Mumbai (India) region — lowest latency for Indian users.

---

## 6. Analysis Worker Deployment

The analysis worker is a long-running process that polls the `jobs` table. It cannot run
as a Vercel serverless function (15-second timeout) and must be deployed separately.

**Options:**

| Option | Cost | Complexity | Best for |
|---|---|---|---|
| **Railway** | ~$5/mo | Low | Hackathon / early stage |
| **Fly.io** | ~$5/mo | Low | Hackathon / early stage |
| **AWS ECS Fargate** | ~$15/mo | Medium | Production |
| **GCP Cloud Run (min-instances=1)** | ~$10/mo | Medium | Production |

### Railway deployment (recommended for SIH demo)

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Deploy from the prototype directory
cd prototype
railway up
```

Set environment variables in Railway dashboard:
```
DATABASE_URL=...
ANTHROPIC_API_KEY=...
```

Worker entry point:
```bash
python3 worker/main.py
```

---

## 7. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: ipsakti_test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r prototype/requirements.txt pytest
      - run: pytest prototype/tests/
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci && npm run lint && npm run type-check

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 8. Database Migration in CI

Migrations run automatically on deploy using a Vercel build hook:

```json
{
  "scripts": {
    "build": "npm run migrate && next build"
  }
}
```

`migrate` script:
```bash
#!/bin/bash
# Run any pending migrations
for f in migrations/V*.sql; do
  echo "Running migration: $f"
  psql $DATABASE_URL < "$f" || exit 1
done
```

---

## 9. Production Checklist

Before going live, verify:

- [ ] All environment variables are set in Vercel (production environment)
- [ ] Database has pgvector extension enabled
- [ ] All migrations have run successfully
- [ ] Statutory corpus is seeded and embedded
- [ ] Clerk production instance is configured (not development)
- [ ] CORS is restricted to the production domain
- [ ] HTTPS is enforced (Vercel handles this automatically)
- [ ] Sentry DSN is set and error reporting is verified
- [ ] Rate limiting is active
- [ ] Worker process is running and picking up jobs
- [ ] `npm audit` returns no high/critical vulnerabilities
- [ ] Test all 5 demo scenarios end-to-end in production environment
- [ ] Test the bad-citation demo to verify the verifier gate works in production

---

## 10. Monitoring & Observability

| What | Tool | Alert threshold |
|---|---|---|
| Error rate | Sentry | Any new error type |
| API response time | Vercel Analytics | p95 > 2s |
| Analysis pipeline duration | Custom structured logs | > 60s per job |
| Worker job queue depth | DB query | > 50 queued jobs |
| LLM provider errors | Sentry | Any 5xx from provider |
| Freshness Monitor staleness | DB query | > 10% of delivered analyses are stale |

### Key metrics to track

```sql
-- Queue depth (should stay near 0)
SELECT COUNT(*) FROM jobs WHERE status = 'queued';

-- Analysis success rate (should be > 85%)
SELECT
  status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM analyses
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Average confidence score by classification
SELECT classification, ROUND(AVG(confidence_score), 3) as avg_confidence
FROM analyses WHERE status = 'delivered'
GROUP BY classification;
```
