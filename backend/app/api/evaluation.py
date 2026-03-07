import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

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
    description=(
        "Loads all settled variables from DB, builds deterministic payload, "
        "optionally runs policy RAG (TX/WA/NC), calls Gemini for recommendation, "
        "validates output, and returns structured JSON for the dashboard."
    ),
)
def evaluate_property(
    evaluation_id: UUID = Path(..., description="UUID of the property_evaluations row"),
    body: EvaluatePropertyRequest = None,
    db: Session = Depends(get_db),
):
    """
    Main AI evaluation endpoint.
    """
    body = body or EvaluatePropertyRequest()
    eval_id_str = str(evaluation_id)

    logger.info("evaluate_property called for evaluation_id=%s force_refresh=%s",
                eval_id_str, body.force_refresh)

    #1. Load evaluation snapshot from DB
    evaluation_data = _load_evaluation_snapshot(db, eval_id_str)
    if not evaluation_data:
        raise HTTPException(status_code=404, detail=f"Evaluation '{eval_id_str}' not found.")

    #2. Fetch user priority ranking
    priority_ranking = _load_priority_ranking(db, evaluation_data)

    #3. Guard: all required variables must be settled
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

    #4. Check for cached AI summary
    if not body.force_refresh:
        cached = _load_cached_summary(db, eval_id_str)
        if cached:
            logger.info("Returning cached AI summary for evaluation_id=%s", eval_id_str)
            return cached

    #5. Run intelligence pipeline
    result = run_intelligence(
        evaluation_id=eval_id_str,
        evaluation_data=evaluation_data,
        priority_ranking=priority_ranking,
        db_session=db,
    )

    #6. Persist to property_ai_summary
    _persist_ai_summary(db, eval_id_str, result)

    #7. Return response
    return result


#DB helpers

def _load_evaluation_snapshot(db: Session, evaluation_id: str) -> dict | None:
    """
    Load the full evaluation snapshot from DB.

    Returns a dict with: property, variables, financials, verdict_color.
    Returns None if evaluation not found.

    NOTE: Replace the stub queries below with your actual ORM models
    once the DB layer is wired up.
    """
    try:
        #Property evaluation row
        eval_row = db.execute(
            "SELECT pe.id, pe.user_id, pe.formula_version_id, pe.status, "
            "       p.formatted_address, p.state, p.zip_code, p.bedrooms, "
            "       p.bathrooms, p.square_feet, p.year_built, p.property_type "
            "FROM property_evaluations pe "
            "JOIN properties p ON p.id = pe.property_id "
            "WHERE pe.id = :eval_id",
            {"eval_id": evaluation_id},
        ).fetchone()

        if not eval_row:
            return None

        #Evaluation components (variables)
        component_rows = db.execute(
            "SELECT component_name, component_payload "
            "FROM evaluation_components "
            "WHERE evaluation_id = :eval_id",
            {"eval_id": evaluation_id},
        ).fetchall()

        variables = {}
        verdict_color = "yellow"  # default
        for row in component_rows:
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

        #Financial metrics
        fin_row = db.execute(
            "SELECT monthly_cash_flow, cap_rate, projected_5yr_roi, estimated_value "
            "FROM evaluation_financials WHERE evaluation_id = :eval_id",
            {"eval_id": evaluation_id},
        ).fetchone()

        financials = {}
        if fin_row:
            financials = {
                "monthly_cash_flow": fin_row["monthly_cash_flow"],
                "cap_rate":          fin_row["cap_rate"],
                "roi_5yr":           fin_row["projected_5yr_roi"],
                "estimated_value":   fin_row["estimated_value"],
            }

        return {
            "evaluation_id": evaluation_id,
            "verdict_color":  verdict_color,
            "property": {
                "formatted_address": eval_row["formatted_address"],
                "state":             eval_row["state"],
                "zip_code":          eval_row["zip_code"],
                "bedrooms":          eval_row["bedrooms"],
                "bathrooms":         eval_row["bathrooms"],
                "square_feet":       eval_row["square_feet"],
                "year_built":        eval_row["year_built"],
                "property_type":     eval_row["property_type"],
            },
            "financials":  financials,
            "variables":   variables,
        }

    except Exception as exc:
        logger.error("Failed to load evaluation snapshot: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load evaluation data.")


def _load_priority_ranking(db: Session, evaluation_data: dict) -> list:
    """
    Load user priority ranking from user_onboarding_profiles.
    Returns empty list if not found (AI will proceed without personalization).
    """
    try:
        user_id = evaluation_data.get("user_id")
        if not user_id:
            return []

        row = db.execute(
            "SELECT priority_ranking FROM user_onboarding_profiles "
            "WHERE user_id = :user_id ORDER BY updated_at DESC LIMIT 1",
            {"user_id": user_id},
        ).fetchone()

        if row and row["priority_ranking"]:
            return row["priority_ranking"]  # JSONB → already a list
        return []

    except Exception as exc:
        logger.warning("Could not load priority ranking: %s", exc)
        return []


def _load_cached_summary(db: Session, evaluation_id: str) -> dict | None:
    """
    Check for an existing validated AI summary in property_ai_summary.
    Returns the parsed summary dict or None.
    """
    try:
        row = db.execute(
            "SELECT summary_json FROM ai_summaries "
            "WHERE evaluation_id = :eval_id AND validated = true "
            "ORDER BY created_at DESC LIMIT 1",
            {"eval_id": evaluation_id},
        ).fetchone()

        if row and row["summary_json"]:
            return row["summary_json"]
        return None

    except Exception as exc:
        logger.warning("Cache lookup failed: %s", exc)
        return None


def _persist_ai_summary(db: Session, evaluation_id: str, result: dict) -> None:
    """
    Store the AI result in ai_summaries table.
    Uses upsert so force_refresh overwrites cleanly.
    """
    try:
        validated = not result.get("admin_review_required", False)
        model_used = (result.get("sources") or {}).get("recommendation_model", "unknown")

        db.execute(
            """
            INSERT INTO ai_summaries (evaluation_id, model_used, summary_json, validated)
            VALUES (:eval_id, :model_used, :summary_json, :validated)
            ON CONFLICT (evaluation_id)
            DO UPDATE SET
                summary_json = EXCLUDED.summary_json,
                model_used   = EXCLUDED.model_used,
                validated    = EXCLUDED.validated,
                created_at   = NOW()
            """,
            {
                "eval_id":      evaluation_id,
                "model_used":   model_used,
                "summary_json": result,
                "validated":    validated,
            },
        )
        db.commit()
        logger.info("AI summary persisted for evaluation_id=%s validated=%s", evaluation_id, validated)

    except Exception as exc:
        logger.error("Failed to persist AI summary: %s", exc)
        db.rollback()