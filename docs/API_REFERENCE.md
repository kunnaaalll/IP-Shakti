# IP-SAKTI — API Reference

**Version:** v1  
**Base URL:** `https://api.ipsakti.in/api/v1`  
**Auth:** Bearer token (Clerk JWT) in `Authorization` header  
**Content-Type:** `application/json`

---

## Authentication

All endpoints except `/statutes/search` and `/statutes/changes` require a valid
Clerk JWT bearer token.

```
Authorization: Bearer <clerk_jwt_token>
```

Unauthenticated requests return `401 Unauthorized`.

---

## Error Format

All errors follow a consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "claims_text exceeds 3000 character limit",
    "field": "claims_text"
  }
}
```

| HTTP Status | Meaning |
|---|---|
| `400` | Validation error — malformed request |
| `401` | Unauthenticated |
| `403` | Forbidden — insufficient role |
| `404` | Resource not found |
| `409` | Conflict — e.g. duplicate in-flight analysis |
| `422` | Unprocessable entity |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | LLM provider unavailable |

---

## Formulations

### `POST /formulations`

Create a new formulation in `draft` status.

**Request body:**
```json
{
  "ingredients": ["ashwagandha", "milk"],
  "extraction_method": "traditional decoction, sun-dried powder",
  "intended_use": "general wellness and stress support",
  "claims_text": "Rejuvenating tonic prepared following traditional method.",
  "jurisdiction": "IN",
  "product_name": "Ashwagandha Churna Blend",
  "notes": "Based on Charaka Samhita formulation",
  "language": "en"
}
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `ingredients` | `string[]` | ✅ | 1–100 items, each ≤ 200 chars |
| `extraction_method` | `string` | ✅ | ≤ 1,000 chars |
| `intended_use` | `string` | ✅ | ≤ 1,000 chars |
| `claims_text` | `string` | ✅ | ≤ 3,000 chars |
| `jurisdiction` | `"IN" \| "INTL"` | ✅ | — |
| `product_name` | `string` | ❌ | ≤ 200 chars |
| `notes` | `string` | ❌ | ≤ 2,000 chars |
| `language` | `string` | ❌ | ISO 639-1 code, default `"en"` |

**Response `201 Created`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "created_at": "2026-09-10T14:00:00Z"
}
```

---

### `PATCH /formulations/{id}`

Update a formulation. Only allowed while `status = "draft"`.

**Request body:** Any subset of the create fields.

**Response `200 OK`:** Updated formulation object.

**Error `409`** if `status ≠ "draft"`.

---

### `DELETE /formulations/{id}`

Soft-delete a formulation. Text fields are purged; metadata is retained for audit.

**Response `204 No Content`**

---

### `GET /formulations/{id}`

Fetch a formulation with its latest analysis summary.

**Response `200 OK`:**
```json
{
  "id": "...",
  "status": "analysed",
  "ingredients": ["ashwagandha", "milk"],
  "extraction_method": "...",
  "intended_use": "...",
  "claims_text": "...",
  "jurisdiction": "IN",
  "latest_analysis": {
    "id": "...",
    "classification": "Classical",
    "confidence_score": 0.7298,
    "status": "delivered",
    "freshness_status": "current",
    "delivered_at": "2026-09-10T14:05:00Z"
  }
}
```

---

## Analyses

### `POST /formulations/{id}/analyze`

Kick off an analysis pipeline. Returns immediately with `202 Accepted`.

**Request body:**
```json
{
  "jurisdiction": "IN"
}
```

**Response `202 Accepted`:**
```json
{
  "analysis_id": "...",
  "status": "queued",
  "message": "Analysis queued. Poll GET /analyses/{analysis_id} for status."
}
```

**Error `409`** if an in-flight analysis already exists for this `(formulation_id, jurisdiction)`.

---

### `POST /formulations/{id}/reanalyze`

Create a new superseding analysis. Allowed when the latest analysis is `delivered` or
`freshness_status = "stale"`. The old analysis is not deleted — it is linked via
`superseded_by_id`.

**Request body:**
```json
{
  "jurisdiction": "IN",
  "reason": "statutory_update"
}
```

**Response `202 Accepted`:** Same shape as `/analyze`.

---

### `GET /analyses/{id}`

Fetch a full analysis with roadmap and citations.

**Response `200 OK`:**
```json
{
  "id": "...",
  "formulation_id": "...",
  "classification": "Classical",
  "classification_trace": [
    "Core ingredient matches a documented classical formulation ('Ashwagandha Churna', Charaka Samhita).",
    "No novel-processing or standardized-fraction language detected."
  ],
  "tkrc_code": "TKRC-A61K-36/00-ASH",
  "tkrc_name": "Ashwagandha Churna",
  "jurisdiction": "IN",
  "confidence_score": 0.7298,
  "status": "delivered",
  "freshness_status": "current",
  "delivered_at": "2026-09-10T14:05:00Z",
  "roadmap": [
    {
      "step": 1,
      "action": "Do not pursue a standard patent on the base formulation.",
      "rationale": "The core formulation matches documented traditional knowledge and is barred as an invention under the Patents Act.",
      "risk_level": "blocker",
      "timeline_note": null,
      "citations": [
        {
          "act": "Patents Act, 1970",
          "section": "3(p)",
          "chunk_id": "PA-3P",
          "text": "An invention which, in effect, is traditional knowledge..."
        }
      ]
    }
  ],
  "disclaimer": "Informational only — not legal advice. For formal IP proceedings, consult a registered patent agent."
}
```

Polling states: `queued` → `processing` → `synthesizing` → `delivered | escalated`.

---

### `GET /analyses/{id}/export.pdf`

Export the analysis roadmap as a formatted PDF.

**Response:** `application/pdf` binary stream  
**Headers:** `Content-Disposition: attachment; filename="ipsakti-analysis-{id}.pdf"`

---

## Escalations

### `POST /escalations`

Manually escalate a delivered analysis for human expert review.

**Request body:**
```json
{
  "analysis_id": "...",
  "reason": "user_requested",
  "notes": "Unusual extraction method not covered by current corpus."
}
```

**Response `201 Created`:**
```json
{
  "escalation_id": "...",
  "status": "pending",
  "message": "Routed to reviewer network. Typical response time: 24–48 hours."
}
```

---

### `GET /escalations/{id}`

Fetch escalation status (for the user who submitted it).

**Response `200 OK`:**
```json
{
  "id": "...",
  "analysis_id": "...",
  "reason": "user_requested",
  "status": "pending | assigned | resolved",
  "resolved_at": null,
  "resolution_notes": null
}
```

---

## Statutes (Public — No Auth Required)

### `GET /statutes/search`

Search the statutory corpus by keyword.

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `q` | `string` | ✅ | Search query |
| `classification` | `string` | ❌ | Filter by classification bucket |
| `jurisdiction` | `string` | ❌ | `IN` or `INTL` |
| `limit` | `integer` | ❌ | Max results, default 10, max 50 |

**Response `200 OK`:**
```json
{
  "results": [
    {
      "chunk_id": "PA-3P",
      "act": "Patents Act, 1970",
      "section": "3(p)",
      "text": "An invention which, in effect, is traditional knowledge...",
      "applies_to": ["Classical"],
      "relevance_score": 0.87
    }
  ],
  "total": 1
}
```

**Rate limit:** 100 requests / hour per IP.

---

### `GET /statutes/changes`

Freshness Monitor feed — returns statutory amendments since a given date.

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `since` | `date` | ✅ | ISO 8601 date, e.g. `2026-01-01` |
| `chunk_id` | `string` | ❌ | Filter to a specific chunk |

**Response `200 OK`:**
```json
{
  "amendments": [
    {
      "chunk_id": "PA-3P",
      "act": "Patents Act, 1970",
      "section": "3(p)",
      "amendment_type": "update",
      "description": "Amended by Patents (Amendment) Act 2026...",
      "gazette_ref": "G.S.R. 123(E)",
      "effective_date": "2026-06-01",
      "detected_at": "2026-06-02T00:00:00Z"
    }
  ]
}
```

---

## Portfolios

### `POST /portfolios`

Create a portfolio.

**Request body:**
```json
{
  "name": "Cohort 2026 — AYUSH Incubator",
  "description": "SIH26 applicant screening batch",
  "is_public": false
}
```

**Response `201 Created`:** Portfolio object with `id`.

---

### `POST /portfolios/{id}/formulations`

Add a formulation to a portfolio.

**Request body:**
```json
{
  "formulation_id": "...",
  "notes": "Promising classical formulation with GI potential"
}
```

**Response `201 Created`**

---

### `GET /portfolios/{id}`

Fetch a portfolio with summary stats for all formulations.

**Response `200 OK`:**
```json
{
  "id": "...",
  "name": "Cohort 2026",
  "formulation_count": 12,
  "formulations": [
    {
      "formulation_id": "...",
      "product_name": "...",
      "classification": "Classical",
      "confidence_score": 0.72,
      "status": "delivered",
      "freshness_status": "current"
    }
  ]
}
```

---

### `GET /gi/overlap`

GI (Geographical Indication) overlap check — returns GI registrations that may conflict
with or complement the formulation's IP strategy.

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `region` | `string` | ✅ | Geographic region, e.g. `"Kerala"` |
| `product` | `string` | ✅ | Product type, e.g. `"churna"` |

**Response `200 OK`:**
```json
{
  "overlapping_gis": [
    {
      "gi_number": "GI/102/2008",
      "name": "Malabar Black Pepper",
      "region": "Kerala",
      "relevance": "Ingredient overlap — black pepper grown in this region may benefit from GI co-branding"
    }
  ]
}
```

---

## Rate Limits

| Endpoint Group | Limit |
|---|---|
| `POST /formulations/{id}/analyze` | 20 / hour per user |
| `GET /statutes/search` | 100 / hour per IP (unauthenticated) |
| `POST /portfolios/{id}/formulations` (batch) | 5 concurrent analyses per portfolio |
| All other authenticated endpoints | 200 / hour per user |

Rate limit headers are returned on every response:
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 18
X-RateLimit-Reset: 1725971400
```
