import logging
from typing import Optional

from .builder import build_base_payload
from .policy import run_policy, SUPPORTED_POLICY_STATES
from .recommendation import run_recommendation, RECOMMENDATION_MODEL
from .validator import validate_ai_output
from .storage import save_ai_summary
from .logger import log_usage

logger = logging.getLogger(__name__)


def generate_ai_recommendation(
    evaluation_id: str,
    evaluation_data: dict,
    priority_ranking: Optional[list] = None,
    user_profile: Optional[dict] = None,
    db_session=None,
) -> dict:
    logger.info("Starting AI intelligence pipeline for evaluation_id=%s", evaluation_id)

    try:
        payload = build_base_payload(
            evaluation_id=evaluation_id,
            evaluation_data=evaluation_data,
            priority_ranking=priority_ranking,
            user_profile=user_profile,
        )
        logger.info(
            "Payload built — data_completeness=%.1f%% failed_vars=%s",
            payload.get("data_completeness_pct", 0),
            payload.get("failed_variables", []),
        )
    except Exception as exc:
        logger.error("Payload build failed for evaluation_id=%s: %s", evaluation_id, exc)
        return _error_response(evaluation_id, f"Payload build failed: {exc}")

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
            if policy_result and policy_result.get("policy_summary"):
                policy_summary = policy_result
                logger.info("Policy stage complete.")
            else:
                logger.info("Policy stage returned empty result — proceeding without policy.")
        except Exception as exc:
            logger.warning("Policy stage failed (non-fatal): %s", exc)
    else:
        logger.info("Policy stage skipped — state '%s' not supported.", state_code)

    try:
        raw_output = run_recommendation(
            payload=payload,
            policy_summary=policy_summary,
        )
        logger.info("Recommendation LLM complete for evaluation_id=%s", evaluation_id)
    except (ValueError, RuntimeError) as exc:
        logger.error("Recommendation LLM failed: %s", exc)
        return _error_response(evaluation_id, f"Recommendation LLM failed: {exc}")

    validated_output = validate_ai_output(
        ai_output=raw_output,
        deterministic_payload=payload,
    )

    if validated_output.get("admin_review_required"):
        logger.warning(
            "Validation failed for evaluation_id=%s — errors: %s",
            evaluation_id,
            validated_output.get("validation_errors"),
        )
    else:
        logger.info("Validation passed for evaluation_id=%s", evaluation_id)

    if db_session:
        try:
            save_ai_summary(
                run_id=evaluation_id,
                property_id=(evaluation_data.get("property") or {}).get("property_id", ""),
                user_id=(evaluation_data.get("property") or {}).get("user_id", ""),
                validated_output=validated_output,
                payload=payload,
                policy_summary=policy_summary,
                db_session=db_session,
            )
        except Exception as exc:
            logger.error("save_ai_summary failed (non-fatal): %s", exc)

    log_usage(
        evaluation_id=evaluation_id,
        model_used=validated_output.get("_meta", {}).get("model", RECOMMENDATION_MODEL),
        policy_summary=policy_summary,
        result=validated_output,
        db_session=db_session,
    )

    return _build_final_response(validated_output, payload, policy_summary)


def _build_final_response(
    validated_output: dict,
    payload: dict,
    policy_summary: Optional[dict],
) -> dict:
    return {
        "status": "admin_review" if validated_output.get("admin_review_required") else "complete",

        "verdict": {
            "color":             validated_output.get("verdict_color"),
            "label":             validated_output.get("verdict_label"),
            "ai_confidence_pct": validated_output.get("ai_confidence_pct"),
            "headline":          validated_output.get("headline"),
            "summary_blurb":     validated_output.get("summary_blurb"),
        },

        "upside_drivers": validated_output.get("key_strengths", []),
        "risk_factors":   validated_output.get("key_risks", []),

        "narratives": {
            "community_profile":      validated_output.get("community_profile"),
            "safety_and_amenities":   validated_output.get("safety_and_amenities"),
            "investment_suitability": validated_output.get("investment_suitability"),
            "verdict_explanation":    validated_output.get("verdict_explanation"),
        },

        "policy_highlights": _extract_policy_highlights(policy_summary),

        "meta": {
            "data_completeness_pct":       payload.get("data_completeness_pct"),
            "missing_data_note":           validated_output.get("missing_data_note"),
            "admin_review_required":       validated_output.get("admin_review_required", False),
            "validation_errors":           validated_output.get("validation_errors", []),
            "validation_warnings":         validated_output.get("validation_warnings", []),
            "subjective_language_warning": validated_output.get("subjective_language_warning"),
        },

        "sources": {
            "recommendation_model": validated_output.get("_meta", {}).get("model"),
            "policy_model":         (policy_summary or {}).get("_meta", {}).get("model"),
            "policy_state":         (policy_summary or {}).get("_meta", {}).get("state"),
        },
    }


def _extract_policy_highlights(policy_summary: Optional[dict]) -> Optional[dict]:
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
    logger.error("Intelligence pipeline error for evaluation_id=%s: %s", evaluation_id, reason)
    return {
        "status":            "error",
        "error":             reason,
        "verdict":           None,
        "upside_drivers":    [],
        "risk_factors":      [],
        "narratives":        None,
        "policy_highlights": None,
        "meta": {
            "admin_review_required": True,
        },
    }