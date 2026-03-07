# Variable — AI Recommendation Engine

**Branch:** `Imene_AIRecommendation`  
**Status:** ✅ Complete  

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
   ├── policy.py          ← LLM 2: RAG policy analysis (TX/WA/NC only)
   ├── recommendation.py  ← LLM 1: tactical data analyst + inject_policy()
   ├── validator.py       ← 4-ruleset deterministic validator
   └── logger.py          ← token + USD cost logging → ai_usage_logs table
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluate-property/{evaluation_id}` | Production — requires DB + real evaluation ID |
| `POST` | `/dev/test-mock` | Dev-only — full pipeline, no DB or API key needed |

### Response Example
```json
{
  "status": "complete",
  "verdict_color": "YELLOW",
  "data_completeness_pct": 90.0,
  "community_profile": "...",
  "safety_and_amenities": "...",
  "investment_suitability": "...",
  "verdict_explanation": "...",
  "key_strengths": ["Cap rate of 5.20% meets investor threshold"],
  "key_risks": ["School score data unavailable — manual verification required"],
  "missing_data_note": "...",
  "policy_highlights": null,
  "admin_review_required": false,
  "validation_errors": [],
  "sources": { "recommendation_model": "gemini-2.0-flash" }
}
```

---

## Validation Rules

| Ruleset | Check | On Fail |
|---|---|---|
| A — Numerical Integrity | AI percentages must match ground-truth payload (±0.6%) | `admin_review_required = true` |
| B — Forbidden Keywords | `recommend`, `guaranteed`, `perfect`, `steal`, etc. | Dashboard warning |
| C — Missing Data Disclaimer | Null variable mentioned → must say `unavailable` / `manual verification` | `admin_review_required = true` |
| D — Verdict Consistency | AI explanation must not contradict verdict color | `admin_review_required = true` |

---

## DB Status

| Table | Status | Notes |
|---|---|---|
| `property_ai_summary` | ✅ exists + tested | AI results written here |
| `ai_usage_logs` | ✅ exists + tested | Token/cost audit confirmed working |
| `policy_documents` | ✅ exists | Policy RAG source |
| `property_evaluations` | ❌ not yet | Waiting on team DB migration |
| `evaluation_components` | ❌ not yet | Waiting on team DB migration |
| `evaluation_financials` | ❌ not yet | Waiting on team DB migration |
| `user_onboarding_profiles` | ❌ not yet | Waiting on team DB migration |

---

## Environment Variables

| Variable | Default |
|---|---|
| `GEMINI_API_KEY` | required |
| `GEMINI_RECOMMENDATION_MODEL` | `gemini-2.0-flash` |
| `GEMINI_POLICY_MODEL` | `gemini-2.0-flash` |
| `SUPABASE_URL` | required |
| `SUPABASE_KEY` | required |

---

## Testing

```bash
cd backend && source venv/bin/activate

# 1. All unit tests (no API key or DB needed)
python test_recommendation.py        # Expected: 4/4 pass ✅

# 2. Swagger endpoint (no API key needed)
uvicorn app.main:app --reload
# POST /dev/test-mock → 200 OK ✅

# 3. DB write to property_ai_summary — confirmed ✅
# 4. DB write to ai_usage_logs — confirmed ✅
```

---

## Known Limitations / Next Steps

- **Policy RAG** — `_pgvector_similarity_search()` in `policy.py` is a stub. Wire up once `policy_documents` embeddings are populated.
- **Production endpoint** — queries ready but blocked on `property_evaluations`, `evaluation_components`, `evaluation_financials` tables being created.
- **Real Gemini calls** — personal key has 0 free-tier quota from DZ region. Needs team shared key or billing.