"""
evaluation.py
-------------
FastAPI router for the AI evaluation endpoint.

Endpoint:
    POST /evaluate-property/{evaluation_id}

Flow:
    1. Load evaluation snapshot from Supabase
    2. Fetch user priority_ranking from user_onboarding_profiles
    3. Guard: all required variables must be settled (ready or failed)
    4. Check for existing cached AI summary (unless force_refresh)
    5. Run intelligence pipeline (engine.py)
    6. Persist result to ai_summaries table
    7. Return structured JSON to dashboard
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from supabase import Client

from app.core.db import get_db
from app.intelligence import run_intelligence
from app.models.evaluation_models import (
    EvaluatePropertyRequest,
    EvaluatePropertyResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate-property", tags=["AI Evaluation"])


@router.post(
    "/{evaluation_id}",
    response_model=EvaluatePropertyResponse,
    summary="Run AI evaluation for a property",
)
def evaluate_property(
    evaluation_id: UUID = Path(..., description="UUID of the property_evaluations row"),
    body: EvaluatePropertyRequest = None,
    db: Client = Depends(get_db),
):
    body = body or EvaluatePropertyRequest()
    eval_id_str = str(evaluation_id)

    logger.info("evaluate_property called — evaluation_id=%s force_refresh=%s",
                eval_id_str, body.force_refresh)

    # ── 1. Load evaluation snapshot ────────────────────────────────────────
    evaluation_data = _load_evaluation_snapshot(db, eval_id_str)
    if not evaluation_data:
        raise HTTPException(status_code=404, detail=f"Evaluation '{eval_id_str}' not found.")

    # ── 2. Fetch user priority ranking ─────────────────────────────────────
    priority_ranking = _load_priority_ranking(db, evaluation_data.get("user_id"))

    # ── 3. Guard: no pending variables ────────────────────────────────────
    pending_vars = [
        name for name, var in evaluation_data.get("variables", {}).items()
        if var.get("status") == "pending"
    ]
    if pending_vars:
        raise HTTPException(
            status_code=202,
            detail={
                "message": "Evaluation not ready — some variables are still pending.",
                "pending_variables": pending_vars,
            },
        )

    # ── 4. Check cache ─────────────────────────────────────────────────────
    if not body.force_refresh:
        cached = _load_cached_summary(db, eval_id_str)
        if cached:
            logger.info("Returning cached AI summary for evaluation_id=%s", eval_id_str)
            return cached

    # ── 5. Run intelligence pipeline ──────────────────────────────────────
    result = run_intelligence(
        evaluation_id=eval_id_str,
        evaluation_data=evaluation_data,
        priority_ranking=priority_ranking,
        db_session=db,
    )

    # ── 6. Persist result ──────────────────────────────────────────────────
    _persist_ai_summary(db, eval_id_str, result)

    return result


# ── DB helpers using Supabase client ──────────────────────────────────────

def _load_evaluation_snapshot(db: Client, evaluation_id: str) -> dict | None:
    """
    Load full evaluation snapshot from Supabase.
    Joins: property_evaluations → properties → evaluation_components → evaluation_financials
    """
    try:
        # ── property_evaluations + properties (via foreign key) ────────────
        eval_resp = db.table("property_evaluations") \
            .select(
                "id, user_id, status, "
                "properties(formatted_address, state, zip_code, bedrooms, "
                "bathrooms, square_feet, year_built, property_type)"
            ) \
            .eq("id", evaluation_id) \
            .single() \
            .execute()

        if not eval_resp.data:
            return None

        eval_row = eval_resp.data
        prop = eval_row.get("properties") or {}

        # ── evaluation_components (variables + verdict) ────────────────────
        comp_resp = db.table("evaluation_components") \
            .select("component_name, component_payload") \
            .eq("evaluation_id", evaluation_id) \
            .execute()

        variables = {}
        verdict_color = "yellow"

        for row in (comp_resp.data or []):
            name    = row["component_name"]
            payload = row["component_payload"] or {}
            if name == "verdict":
                verdict_color = payload.get("color", "yellow")
            else:
                variables[name] = {
                    "status":     payload.get("status", "ready"),
                    "value":      payload.get("value"),
                    "source":     payload.get("source"),
                    "fetched_at": payload.get("fetched_at"),
                }

        # ── evaluation_financials ──────────────────────────────────────────
        fin_resp = db.table("evaluation_financials") \
            .select("monthly_cash_flow, cap_rate, projected_5yr_roi, estimated_value") \
            .eq("evaluation_id", evaluation_id) \
            .maybe_single() \
            .execute()

        fin = fin_resp.data or {}

        return {
            "evaluation_id": evaluation_id,
            "user_id":        eval_row.get("user_id"),
            "verdict_color":  verdict_color,
            "property": {
                "formatted_address": prop.get("formatted_address"),
                "state":             prop.get("state"),
                "zip_code":          prop.get("zip_code"),
                "bedrooms":          prop.get("bedrooms"),
                "bathrooms":         prop.get("bathrooms"),
                "square_feet":       prop.get("square_feet"),
                "year_built":        prop.get("year_built"),
                "property_type":     prop.get("property_type"),
            },
            "financials": {
                "monthly_cash_flow": fin.get("monthly_cash_flow"),
                "cap_rate":          fin.get("cap_rate"),
                "roi_5yr":           fin.get("projected_5yr_roi"),
                "estimated_value":   fin.get("estimated_value"),
            },
            "variables": variables,
        }

    except Exception as exc:
        logger.error("Failed to load evaluation snapshot: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load evaluation data.")


def _load_priority_ranking(db: Client, user_id: str | None) -> list:
    """Load user priority ranking from user_onboarding_profiles."""
    if not user_id:
        return []
    try:
        resp = db.table("user_onboarding_profiles") \
            .select("priority_ranking") \
            .eq("user_id", user_id) \
            .order("updated_at", desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()

        if resp.data and resp.data.get("priority_ranking"):
            return resp.data["priority_ranking"]
        return []

    except Exception as exc:
        logger.warning("Could not load priority ranking: %s", exc)
        return []


def _load_cached_summary(db: Client, evaluation_id: str) -> dict | None:
    """Check for an existing validated AI summary in ai_summaries."""
    try:
        resp = db.table("ai_summaries") \
            .select("summary_json") \
            .eq("evaluation_id", evaluation_id) \
            .eq("validated", True) \
            .order("created_at", desc=True) \
            .limit(1) \
            .maybe_single() \
            .execute()

        if resp.data and resp.data.get("summary_json"):
            return resp.data["summary_json"]
        return None

    except Exception as exc:
        logger.warning("Cache lookup failed: %s", exc)
        return None


def _persist_ai_summary(db: Client, evaluation_id: str, result: dict) -> None:
    """Store AI result in property_ai_summary table using upsert."""
    try:
        db.table("property_ai_summary").upsert({
            "evaluation_id":         evaluation_id,
            "property_id":           result.get("property_id", ""),
            "recommendation":        result.get("verdict_color"),
            "traffic_light":         result.get("verdict_color"),
            "confidence_score":      result.get("data_completeness_pct"),
            "summary":               result.get("verdict_explanation"),
            "full_output":           result,
            "admin_review_required": result.get("admin_review_required", False),
        }, on_conflict="evaluation_id").execute()

        logger.info("AI summary persisted — evaluation_id=%s", evaluation_id)

    except Exception as exc:
        logger.error("Failed to persist AI summary: %s", exc)
