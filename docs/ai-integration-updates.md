# AI Integration Updates

This document records the backend fixes made to get the new AI recommendation flow working in `SecondIntegration`.

## Summary

The teammate-provided AI package in `backend/app/ai/` was added successfully, but the integration did not run cleanly at first because the current app code, dependencies, and live Supabase schema were not fully aligned with that implementation.

The updates below were made to bridge those gaps.

## Changes Made

### 1. Fixed AI summary table compatibility

Files updated:
- `backend/app/services/analysis_repository.py`
- `backend/app/ai/storage.py`

Problem:
- The code expected `property_ai_summaries`.
- The live PostgREST schema exposed `property_ai_summary`.
- The older singular table also appears to use a different column layout than the newer design.

Fix:
- Added fallback support for both table names:
  - `property_ai_summaries`
  - `property_ai_summary`
- Added progressive query fallback for dashboard reads:
  - query by `run_id`
  - then by `property_id` + `user_id`
  - then by `property_id` only
- Added write fallback in AI storage so inserts can tolerate older table variants that do not support `run_id`.

Why:
- This prevents the dashboard and AI-save path from crashing when the Supabase project is on an older AI summary schema.

### 2. Fixed missing Supabase import in AI trigger route

File updated:
- `backend/app/api/routes/analysis.py`

Problem:
- `POST /api/property/analyze/{run_id}/ai` used `supabase` without importing it.

Fix:
- Imported `supabase` from `app.core.supabase_client`.
- Preserved `HTTPException` handling so route-level 404s are not converted into generic 500s.

Why:
- This unblocked the AI trigger endpoint and made route errors behave correctly.

### 3. Added missing Gemini SDK dependency

Files updated:
- `backend/requirements.txt`
- `backend/app/ai/recommendation.py`
- `backend/app/ai/policy.py`

Problem:
- The AI code imports:
  - `from google import genai`
  - `from google.genai import types`
- The backend environment did not include the `google-genai` package.

Fix:
- Added `google-genai` to `backend/requirements.txt`.
- Updated the AI modules to fail or skip cleanly when the Gemini SDK is not installed, instead of crashing during import.

Why:
- This makes the dependency requirement explicit and gives clearer runtime behavior.

### 4. Fixed onboarding priority formatting for AI prompts

File updated:
- `backend/app/ai/recommendation.py`

Problem:
- The onboarding priorities were normalized into dicts like:
  - `{"rank": 1, "factor": "cash flow"}`
- The prompt builder still assumed priorities were strings and tried to call `", ".join(...)` on dicts.

Fix:
- Updated the formatter to support:
  - list of strings
  - list of dicts
  - mixed/unknown values safely

Why:
- This resolved the `expected str instance, dict found` error during AI recommendation generation.

## Endpoints Affected

These fixes were made around the following routes:

- `POST /api/property/analyze`
- `POST /api/property/analyze/{run_id}/ai`
- `GET /api/dashboard/property/{property_id}?user_id={user_id}`
- `GET /api/property/analyze/{run_id}`
- `GET /api/property/recent-searches`

## Current Expectations

For the AI endpoint to work end-to-end, the active backend environment still needs:

- `google-genai` installed
- `GEMINI_API_KEY` configured in `backend/.env`
- a valid Supabase schema for the AI summary table

## Remaining Risk

The current code now tolerates multiple AI summary schema shapes, but that is a compatibility layer, not the ideal final state.

The cleaner long-term fix is to standardize the Supabase schema and codebase on a single canonical AI summary table definition, then remove the legacy fallbacks.

## Recommended Follow-Up

1. Inspect the actual Supabase definition of `property_ai_summary` / `property_ai_summaries`.
2. Choose one canonical table shape.
3. Add a migration for that table.
4. Remove compatibility fallbacks once the DB is aligned.
5. Add backend tests for:
   - dashboard payload assembly
   - AI trigger route
   - AI summary persistence
