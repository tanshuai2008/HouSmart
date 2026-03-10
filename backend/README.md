# Variable — AI Recommendation Engine

**Branch:** `Imene_AIRecommendation`  
**Status:** ✅ Complete — Demo Ready  
**Models:** LLM 1 → `gemini-2.5-flash` | LLM 2 (Policy RAG) → `gemini-3-flash-preview`

---

## What This Does

Implements the core LLM intelligence pipeline for HouSmart property evaluations.  
When all property variables are settled (`ready` or `failed`), this module builds a deterministic JSON payload, optionally runs policy RAG analysis (TX/WA/NC), calls Gemini for a structured investment recommendation, validates the output, logs usage, and returns structured JSON to the dashboard.

---

## Task Spec Coverage

| Requirement | File | Status |
|---|---|---|
| `recommendation.py` → deterministic JSON + optional policy | `intelligence/recommendation.py` | ✅ |
| `inject_policy()` helper | `intelligence/recommendation.py` | ✅ |
| `engine.py` → conditional policy + recommendation + logging | `intelligence/engine.py` | ✅ |
| Valid structured JSON output enforced | `recommendation.py` + `validator.py` | ✅ |
| Failed variable flags passed to AI | `intelligence/builder.py` | ✅ |
| Post-AI deterministic validation (4 rulesets) | `intelligence/validator.py` | ✅ |
| Token + cost audit logging to `ai_usage_logs` | `intelligence/logger.py` | ✅ tested |
| Versioned prompt files | `intelligence/prompts/` | ✅ |
| API endpoint + Pydantic schemas | `api/evaluation.py` + `models/evaluation_models.py` | ✅ |
| DB write to `property_ai_summary` | `api/evaluation.py` | ✅ tested |
| Real user priorities from `user_onboarding_answers` | `api/test_endpoint.py` | ✅ tested |
| Policy RAG with real Supabase data | `intelligence/policy.py` | ✅ tested (text fallback) |
| Two-model pipeline end-to-end | `engine.py` | ✅ confirmed working |

---

## Architecture

```
POST /evaluate-property/{evaluation_id}
        │
        ▼
   evaluation.py          ← loads DB snapshot, guards pending vars, checks cache
        │
        ▼
   engine.py              ← main AI orchestrator
   │
   ├── builder.py         ← deterministic JSON (ready + failed vars + priorities)
   ├── policy.py          ← LLM 2: RAG policy (TX/WA/NC) — text fallback when no embeddings
   ├── recommendation.py  ← LLM 1: tactical data analyst + inject_policy()
   ├── validator.py       ← 4-ruleset deterministic validator
   └── logger.py          ← token + USD cost logging → ai_usage_logs table
```

### Two-Model Strategy

| Model | Role | Runs |
|---|---|---|
| `gemini-2.5-flash` | LLM 1 — Tactical Data Analyst | Always |
| `gemini-3-flash-preview` | LLM 2 — Policy Expert | TX / WA / NC only |
| Python script | Deterministic Validator | Always (post-AI) |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluate-property/{evaluation_id}` | Production endpoint |
| `GET` | `/dev/properties` | List all properties available for testing |
| `POST` | `/dev/test-mock` | Mocked LLM — no API key or DB needed |
| `POST` | `/dev/test-real` | Real Gemini + Supabase — Houston TX default |
| `POST` | `/dev/test-real/{property_id}` | Real Gemini + Supabase — any property |

---

## Running for Demo

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs**

### Demo Flow (Swagger UI)

**Step 1 — See available properties:**
```
GET /dev/properties → Execute
```
Copy any `id` from the response.

**Step 2a — Quick demo (no API key needed):**
```
POST /dev/test-mock → Execute
```
Returns full structured AI recommendation instantly.

**Step 2b — Full real demo (requires GEMINI_API_KEY in .env):**
```
POST /dev/test-real/{paste_property_id} → Execute
```
- Fetches real variables from Supabase
- Loads real user priorities from `user_onboarding_answers`
- Calls `gemini-2.5-flash` for recommendation
- Calls `gemini-3-flash-preview` for TX policy analysis
- Returns full structured JSON with `policy_highlights` populated

### Expected Response
```json
{
  "status": "complete",
  "verdict_color": "YELLOW",
  "data_completeness_pct": 60,
  "community_profile": "...",
  "safety_and_amenities": "...",
  "investment_suitability": "...",
  "verdict_explanation": "...",
  "key_strengths": ["Excellent school quality (score 100/100)", "..."],
  "key_risks": ["Crime score unavailable", "Very high noise levels (score 20/100)"],
  "missing_data_note": "...",
  "policy_highlights": {
    "state": "TX",
    "summary": "Texas has no state income tax...",
    "threats": ["Commercial properties subject to standard appraisal increases"],
    "opportunities": ["Homestead exemption increased to $100,000"],
    "key_obligations": ["Short-term rentals require city permits in Houston"],
    "str_restrictions": "Houston requires permits and hotel occupancy tax for STRs"
  },
  "admin_review_required": false,
  "sources": {
    "recommendation_model": "gemini-2.5-flash",
    "policy_model": "gemini-3-flash-preview",
    "policy_state": "TX"
  }
}
```

---

## File Structure

```
backend/app/
├── api/
│   ├── evaluation.py               ← POST /evaluate-property/{evaluation_id}
│   └── test_endpoint.py            ← GET+POST /dev/* (DEV ONLY)
├── core/
│   ├── config.py
│   ├── db.py                       ← FastAPI dependency (wraps supabase_client)
│   └── supabase_client.py          ← Shared Supabase client
├── models/
│   └── evaluation_models.py        ← Pydantic schemas
└── intelligence/
    ├── engine.py                    ← Main orchestrator
    ├── builder.py                   ← Deterministic payload builder
    ├── recommendation.py            ← LLM 1 (gemini-2.5-flash)
    ├── policy.py                    ← LLM 2 (gemini-3-flash-preview) + text fallback
    ├── validator.py                 ← 4-ruleset validator
    ├── logger.py                    ← Token + cost audit
    └── prompts/
        ├── recommendation_v1.txt
        └── policy_v1.txt
```

---

## Validation Rules

| Ruleset | Check | On Fail |
|---|---|---|
| A — Numerical Integrity | AI % values must match ground-truth (±0.6%) | `admin_review_required = true` |
| B — Forbidden Keywords | `recommend`, `guaranteed`, `perfect`, `steal`, etc. | Dashboard warning |
| C — Missing Data Disclaimer | Null variable mentioned → must include `unavailable` | `admin_review_required = true` |
| D — Verdict Consistency | AI explanation must not contradict verdict color | `admin_review_required = true` |

---

## Environment Variables

```env
GEMINI_API_KEY=your_key
GEMINI_RECOMMENDATION_MODEL=gemini-2.5-flash
GEMINI_POLICY_MODEL=gemini-3-flash-preview
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

---

## DB Status

| Table | Status | Used For |
|---|---|---|
| `property_ai_summary` | ✅ tested | AI results |
| `ai_usage_logs` | ✅ tested | Token + cost audit |
| `policy_documents` | ✅ has test data (TX) | Policy RAG |
| `transit_scores` | ✅ has data | Transit variable |
| `flood_zones` | ✅ has data | Flood variable |
| `noise_scores` | ✅ has data | Noise variable |
| `osm_poi_cache` | ✅ has data | Amenity variable |
| `rent_estimate_cache` | ✅ has data | Rent variable |
| `school_rankings` | ✅ has data | School variable |
| `redfin_median_prices` | ✅ has data | Median home value |
| `geo_tract_metrics` | ✅ has data | Census metrics |
| `user_onboarding_answers` | ✅ has data | User priorities |
| `property_evaluations` | ❌ pending | Waiting on team DB migration |

---

## Known Limitations / Next Steps

- **Policy RAG** — currently uses text fallback from `policy_documents`. pgVector similarity search ready in `policy.py` for Phase 13.
- **Production endpoint** — waiting on `property_evaluations`, `evaluation_components`, `evaluation_financials` tables.
- **Prompt v2** — planned once user preferences front end is integrated.
- **Crime score** — not yet in DB, flagged as `failed` and handled gracefully by AI.