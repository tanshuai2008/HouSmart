import logging

from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

AI_SUMMARY_TABLE_NAMES = ("property_ai_summaries", "property_ai_summary")


def save_ai_summary(
    run_id: str,
    property_id: str,
    user_id: str,
    validated_output: dict,
    payload: dict,
    policy_summary: dict | None,
    db_session,
) -> None:
    meta = validated_output.get("_meta", {})

    row = {
        "run_id":                   run_id,
        "property_id":              property_id,
        "user_id":                  user_id,
        "verdict_color":            validated_output.get("verdict_color"),
        "verdict_label":            validated_output.get("verdict_label"),
        "ai_confidence_pct":        validated_output.get("ai_confidence_pct"),
        "headline":                 validated_output.get("headline"),
        "summary_blurb":            validated_output.get("summary_blurb"),
        "community_profile":        validated_output.get("community_profile"),
        "safety_and_amenities":     validated_output.get("safety_and_amenities"),
        "investment_suitability":   validated_output.get("investment_suitability"),
        "verdict_explanation":      validated_output.get("verdict_explanation"),
        "key_strengths":            validated_output.get("key_strengths"),
        "key_risks":                validated_output.get("key_risks"),
        "data_completeness_pct":    payload.get("data_completeness_pct"),
        "missing_data_note":        validated_output.get("missing_data_note"),
        "admin_review_required":    validated_output.get("admin_review_required", False),
        "validation_errors":        validated_output.get("validation_errors", []),
        "validation_warnings":      validated_output.get("validation_warnings", []),
        "model_used":               meta.get("model"),
        "policy_injected":          meta.get("policy_injected", False),
        "policy_state":             (policy_summary or {}).get("_meta", {}).get("state"),
    }
    legacy_row = dict(row)
    legacy_row.pop("run_id", None)

    try:
        for table_name in AI_SUMMARY_TABLE_NAMES:
            try:
                db_session.table(table_name).insert(row).execute()
                logger.info("AI summary saved for run_id=%s in %s", run_id, table_name)
                return
            except APIError as exc:
                if exc.code == "42703":
                    db_session.table(table_name).insert(legacy_row).execute()
                    logger.info("AI summary saved for property_id=%s user_id=%s in %s", property_id, user_id, table_name)
                    return
                if exc.code != "PGRST205":
                    raise
        raise RuntimeError("AI summary table not found in Supabase schema cache")
    except Exception as exc:
        logger.error("Failed to save AI summary for run_id=%s: %s", run_id, exc)
        raise
