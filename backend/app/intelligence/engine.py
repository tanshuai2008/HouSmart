import logging
from typing import Optional

from .builder import build_base_payload
from .policy import run_policy, SUPPORTED_POLICY_STATES
from .recommendation import run_recommendation
from .validator import validate_ai_output
from .logger import log_usage

logger = logging.getLogger(__name__)


def run_intelligence(
    evaluation_id: str,
    evaluation_data: dict,
    priority_ranking: Optional[list] = None,
    db_session=None,
) -> dict:
    """
    Main AI orchestrator. Coordinates all intelligence sub-modules and
    returns a validated structured JSON ready for the dashboard.

    Args:
        evaluation_id:    Unique ID for this property evaluation.
        evaluation_data:  Full snapshot dict from the DB, containing:
                            - property (address, lat, lng, state, ...)
                            - variables (each with status + value)
                            - financials (cap_rate, cash_flow, roi_5yr, ...)
                            - verdict_color ("green" | "yellow" | "red")
        priority_ranking: User's priority list from user_onboarding_profiles.
                          e.g. [{"factor": "roi", "rank": 1}, ...]
        db_session:       Optional DB session for policy RAG retrieval and logging.

    Returns:
        Validated structured dict with recommendation, policy highlights,
        validation metadata, and admin_review_required flag.
    """
    logger.info("Starting AI intelligence pipeline for evaluation_id=%s", evaluation_id)

    #Step 1: Build deterministic payload
    try:
        payload = build_base_payload(
            evaluation_data=evaluation_data,
            priority_ranking=priority_ranking,
        )
        logger.info(
            "Payload built — data_completeness=%.1f%% failed_vars=%s",
            payload.get("data_completeness_pct", 0),
            payload.get("failed_variables", []),
        )
    except Exception as exc:
        logger.error("Payload build failed for evaluation_id=%s: %s", evaluation_id, exc)
        return _error_response(evaluation_id, f"Payload build failed: {exc}")

    #Step 2: Optional policy stage
    state_code     = (evaluation_data.get("property") or {}).get("state", "")
    policy_summary: Optional[dict] = None

    if state_code in SUPPORTED_POLICY_STATES:
        logger.info("Policy stage: running for state=%s", state_code)
        try:
            policy_result = run_policy(
                evaluation_id=evaluation_id,
                state_code=state_code,
                db_session=db_session,
            )
            # Only use policy result if it has meaningful content
            if policy_result and policy_result.get("policy_summary"):
                policy_summary = policy_result
                logger.info("Policy stage complete — summary obtained.")
            else:
                logger.info("Policy stage returned empty result — proceeding without policy.")
        except Exception as exc:
            # Policy is non-fatal — log and continue
            logger.warning("Policy stage failed (non-fatal): %s", exc)
    else:
        logger.info("Policy stage skipped — state '%s' not in supported list.", state_code)

    #Step 3: Run recommendation LLM
    try:
        raw_output = run_recommendation(
            payload=payload,
            policy_summary=policy_summary,
        )
        logger.info("Recommendation LLM complete for evaluation_id=%s", evaluation_id)
    except (ValueError, RuntimeError) as exc:
        logger.error("Recommendation LLM failed: %s", exc)
        return _error_response(evaluation_id, f"Recommendation LLM failed: {exc}")

    #Step 4: Validate output
    validated_output = validate_ai_output(
        ai_output=raw_output,
        deterministic_payload=payload,
    )

    if validated_output.get("admin_review_required"):
        logger.warning(
            "Validation failed for evaluation_id=%s — flagged for admin review. Errors: %s",
            evaluation_id,
            validated_output.get("validation_errors"),
        )
    else:
        logger.info("Validation passed for evaluation_id=%s", evaluation_id)

    #Step 5: Log usage
    log_usage(
        evaluation_id=evaluation_id,
        model_used=validated_output.get("_meta", {}).get("model", "gemini-1.5-flash"),
        policy_summary=policy_summary,
        result=validated_output,
        db_session=db_session,
    )

    #Step 6: Clean and return
    return _build_final_response(validated_output, payload, policy_summary)


def _build_final_response(
    validated_output: dict,
    payload: dict,
    policy_summary: Optional[dict],
) -> dict:
    """
    Assemble the final dashboard-ready response.
    Strips internal metadata (_meta) before returning.
    """
    # Pull the structured AI sections
    response = {
        "status": "admin_review" if validated_output.get("admin_review_required") else "complete",
        "verdict_color":        payload.get("verdict_color"),
        "data_completeness_pct": payload.get("data_completeness_pct"),

        # AI-generated sections
        "community_profile":    validated_output.get("community_profile"),
        "safety_and_amenities": validated_output.get("safety_and_amenities"),
        "investment_suitability": validated_output.get("investment_suitability"),
        "verdict_explanation":  validated_output.get("verdict_explanation"),
        "key_strengths":        validated_output.get("key_strengths", []),
        "key_risks":            validated_output.get("key_risks", []),
        "missing_data_note":    validated_output.get("missing_data_note"),

        # Policy section — only if policy ran and has content
        "policy_highlights": _extract_policy_highlights(policy_summary),

        # Validation metadata
        "admin_review_required":     validated_output.get("admin_review_required", False),
        "validation_errors":         validated_output.get("validation_errors", []),
        "validation_warnings":       validated_output.get("validation_warnings", []),
        "subjective_language_warning": validated_output.get("subjective_language_warning"),

        # Source attribution
        "sources": {
            "recommendation_model": validated_output.get("_meta", {}).get("model"),
            "policy_model": (policy_summary or {}).get("_meta", {}).get("model"),
            "policy_state": (policy_summary or {}).get("_meta", {}).get("state"),
        },
    }

    return response

def _extract_policy_highlights(policy_summary: Optional[dict]) -> Optional[dict]:
    """Return a clean policy highlights dict for the dashboard, or None."""
    if not policy_summary or not policy_summary.get("policy_summary"):
        return None

    raw = policy_summary.get("policy_summary", "")

    parsed = {}
    if isinstance(raw, str):
        clean = raw.strip()
        if clean.startswith("{"):
            try:
                import json
                parsed = json.loads(clean)
            except Exception:
                parsed = {"summary": clean}
        else:
            parsed = {"summary": clean}
    elif isinstance(raw, dict):
        parsed = raw

    return {
        "state":            parsed.get("state") or policy_summary.get("_meta", {}).get("state"),
        "summary":          parsed.get("summary") or raw,
        "threats":          parsed.get("threats", []),
        "opportunities":    parsed.get("opportunities", []),
        "key_obligations":  parsed.get("key_obligations", []),
        "str_restrictions": parsed.get("str_restrictions"),
    }

def _error_response(evaluation_id: str, reason: str) -> dict:
    """Return a structured error response that the dashboard can handle gracefully."""
    logger.error("Intelligence pipeline error for evaluation_id=%s: %s", evaluation_id, reason)
    return {
        "status":                  "error",
        "error":                   reason,
        "admin_review_required":   True,
        "verdict_color":           None,
        "community_profile":       None,
        "safety_and_amenities":    None,
        "investment_suitability":  None,
        "verdict_explanation":     None,
        "key_strengths":           [],
        "key_risks":               [],
        "policy_highlights":       None,
    }