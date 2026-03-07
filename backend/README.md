# Variable — AI Recommendation Engine

**Branch:** `Imene_AIRecommendation`  
**Status:** ✅ Complete  
**Endpoint tested:** `POST /dev/test-mock` → 200 OK via Swagger

---

## What This Does

Implements the **core LLM intelligence pipeline** for HouSmart property evaluations, as specified in the AI Pipeline doc.

When all property variables are settled (status = `ready` or `failed`), this module:
1. Builds a deterministic JSON payload from the DB snapshot
2. Optionally runs a policy RAG analysis (TX / WA / NC only)
3. Calls Gemini to generate a structured investment recommendation
4. Validates the output deterministically (no LLM 3 for MVP)
5. Logs token usage and cost
6. Returns structured JSON to the dashboard

---

## Task Spec Coverage

| Requirement | File | Status |
|---|---|---|
| `recommendation.py` → receives deterministic JSON + optional policy | `intelligence/recommendation.py` | ✅ |
| `inject_policy()` helper | `intelligence/recommendation.py` | ✅ |
| `engine.py` → conditional policy + mandatory recommendation + logging | `intelligence/engine.py` | ✅ |
| Valid structured JSON output enforced | `recommendation.py` + `validator.py` | ✅ |
| Failed variable flags passed to AI | `intelligence/builder.py` | ✅ |
| Post-AI deterministic validation | `intelligence/validator.py` | ✅ |
| Token + cost audit logging | `intelligence/logger.py` | ✅ |
| Versioned prompt files | `intelligence/prompts/` | ✅ |
| API endpoint + Pydantic schemas | `api/evaluation.py` + `models/evaluation_models.py` | ✅ |

> `services/evaluation_orchestrator.py` (DB polling / variable timing) is out of scope for this task — belongs to the variable pipeline integration phase.

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
   ├── builder.py         ← builds deterministic JSON (ready + failed vars + priorities)
   ├── policy.py          ← LLM 2: RAG policy analysis (TX/WA/NC only)
   ├── recommendation.py  ← LLM 1: tactical data analyst + inject_policy()
   ├── validator.py       ← Python deterministic validation (4 rulesets)
   └── logger.py          ← token + USD cost logging to ai_usage_log table
```

### Two-Model Strategy

| Model | Role | Runs |
|---|---|---|
| `gemini-2.0-flash` | LLM 1 — Tactical Data Analyst | Always |
| `gemini-2.0-flash` | LLM 2 — Strategic Policy Expert | TX / WA / NC only |
| Python script | Deterministic Validator | Always (post-AI) |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/evaluate-property/{evaluation_id}` | Production — requires DB + real evaluation ID |
| `POST` | `/dev/test-mock` | Dev-only — full pipeline with mocked LLM, no DB or API key needed |

### Response Schema
```json
{
  "status": "complete",
  "verdict_color": "YELLOW",
  "data_completeness_pct": 90.0,
  "community_profile": "...",
  "safety_and_amenities": "...",
  "investment_suitability": "...",
  "verdict_explanation": "...",
  "key_strengths": ["..."],
  "key_risks": ["..."],
  "missing_data_note": "...",
  "policy_highlights": null,
  "admin_review_required": false,
  "validation_errors": [],
  "validation_warnings": [],
  "sources": {
    "recommendation_model": "gemini-2.0-flash",
    "policy_model": null,
    "policy_state": null
  }
}
```

---

## File Structure

```
backend/app/
├── api/
│   ├── evaluation.py               ← POST /evaluate-property/{evaluation_id}
│   └── test_endpoint.py            ← POST /dev/test-mock (DEV ONLY)
├── core/
│   └── db.py                       ← DB session stub (replace with Supabase connection)
├── models/
│   └── evaluation_models.py        ← Pydantic request/response schemas
└── intelligence/
    ├── __init__.py
    ├── engine.py                    ← Main orchestrator
    ├── builder.py                   ← Deterministic payload builder
    ├── recommendation.py            ← LLM 1 + inject_policy()
    ├── policy.py                    ← LLM 2 + pgVector RAG stub
    ├── validator.py                 ← 4-ruleset deterministic validator
    ├── logger.py                    ← Token + cost audit logger
    └── prompts/
        ├── recommendation_v1.txt
        └── policy_v1.txt
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

## Environment Variables

| Variable | Default |
|---|---|
| `GEMINI_API_KEY` | required |
| `GEMINI_RECOMMENDATION_MODEL` | `gemini-2.0-flash` |
| `GEMINI_POLICY_MODEL` | `gemini-2.0-flash` |
| `GEMINI_MAX_TOKENS` | `1500` |
| `GEMINI_TEMPERATURE` | `0.2` |
| `RAG_TOP_K` | `5` |

---

## Running & Testing

```bash
cd backend && source venv/bin/activate

# 1. Run all unit tests (no API key needed)
python test_recommendation.py        # Expected: 4/4 pass

# 2. Test via Swagger (no API key needed)
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000/docs → POST /dev/test-mock → Execute
# Expected: 200 OK with full structured JSON

# 3. Real Gemini call (requires valid key with quota)
export GEMINI_API_KEY=your_key_here
python test_recommendation.py
```

---

## Known Limitations / Next Steps

- **Policy RAG** — `_pgvector_similarity_search()` in `policy.py` is a stub. Wire up once `policy_embeddings` table is populated (Phase 13).
- **`db.py`** — stub only. Replace with real Supabase/SQLAlchemy session for production endpoint.
- **`evaluation_orchestrator.py`** — variable polling → AI trigger is a separate service task.
- **Real Gemini calls** — personal key has 0 free-tier quota from DZ region. Needs team shared key or billing.