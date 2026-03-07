import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Approximate cost per 1M tokens (USD)
# Update these when Gemini pricing changes.
COST_PER_1M_INPUT_TOKENS: dict[str, float] = {
    "gemini-1.5-flash":   0.075,   # input
    "gemini-1.5-pro":     1.25,    # input
}
COST_PER_1M_OUTPUT_TOKENS: dict[str, float] = {
    "gemini-1.5-flash":   0.30,
    "gemini-1.5-pro":     5.00,
}


def log_usage(
    evaluation_id: str,
    model_used: str,
    policy_summary: Optional[dict],
    result: dict,
    db_session=None,
) -> None:
    """
    Log AI usage metrics for audit and cost tracking.

    Args:
        evaluation_id:  The evaluation this call belongs to.
        model_used:     Primary model name (recommendation model).
        policy_summary: Policy result dict (may contain its own _meta).
        result:         Validated AI output (contains _meta with token counts).
        db_session:     Optional DB session for writing to ai_usage_log table.
    """
    try:
        # ── Extract recommendation model usage ────────────────────────────
        rec_meta = result.get("_meta", {})
        rec_input_tokens  = rec_meta.get("input_tokens", 0)
        rec_output_tokens = rec_meta.get("output_tokens", 0)
        rec_model         = rec_meta.get("model", model_used)

        # ── Extract policy model usage (if ran) ───────────────────────────
        pol_meta = (policy_summary or {}).get("_meta", {})
        pol_input_tokens  = pol_meta.get("input_tokens", 0)
        pol_output_tokens = pol_meta.get("output_tokens", 0)
        pol_model         = pol_meta.get("model")
        policy_ran        = bool(pol_meta)

        # ── Compute costs ─────────────────────────────────────────────────
        rec_cost = _compute_cost(rec_model, rec_input_tokens, rec_output_tokens)
        pol_cost = _compute_cost(pol_model, pol_input_tokens, pol_output_tokens) if policy_ran else 0.0
        total_cost = round(rec_cost + pol_cost, 6)

        usage_record = {
            "evaluation_id":        evaluation_id,
            "recommendation_model": rec_model,
            "rec_input_tokens":     rec_input_tokens,
            "rec_output_tokens":    rec_output_tokens,
            "rec_cost_usd":         round(rec_cost, 6),
            "policy_ran":           policy_ran,
            "policy_model":         pol_model,
            "pol_input_tokens":     pol_input_tokens,
            "pol_output_tokens":    pol_output_tokens,
            "pol_cost_usd":         round(pol_cost, 6),
            "total_cost_usd":       total_cost,
            "admin_review_required": result.get("admin_review_required", False),
            "validation_errors":    result.get("validation_errors", []),
            "logged_at":            datetime.now(timezone.utc).isoformat(),
        }

        # ── Write to DB ───────────────────────────────────────────────────
        if db_session:
            _write_to_db(db_session, usage_record)
        else:
            # Dev fallback: log to console
            logger.info("AI Usage [evaluation_id=%s]: %s", evaluation_id, usage_record)

    except Exception as exc:
        # Never let logging failure break the response
        logger.error("Failed to log AI usage for evaluation_id=%s: %s", evaluation_id, exc)


def _compute_cost(model: Optional[str], input_tokens: int, output_tokens: int) -> float:
    """Compute estimated cost in USD for a model call."""
    if not model:
        return 0.0
    input_cost  = (input_tokens  / 1_000_000) * COST_PER_1M_INPUT_TOKENS.get(model, 0.0)
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS.get(model, 0.0)
    return input_cost + output_cost


def _write_to_db(db_session, record: dict) -> None:
    """
    Write usage record to the ai_usage_log table.

    NOTE: This uses a raw INSERT for now.
    Replace with your actual ORM/asyncpg pattern when integrated.
    """
    try:
        db_session.execute(
            """
            INSERT INTO ai_usage_log (
                evaluation_id, recommendation_model, rec_input_tokens,
                rec_output_tokens, rec_cost_usd, policy_ran, policy_model,
                pol_input_tokens, pol_output_tokens, pol_cost_usd,
                total_cost_usd, admin_review_required, validation_errors, logged_at
            ) VALUES (
                :evaluation_id, :recommendation_model, :rec_input_tokens,
                :rec_output_tokens, :rec_cost_usd, :policy_ran, :policy_model,
                :pol_input_tokens, :pol_output_tokens, :pol_cost_usd,
                :total_cost_usd, :admin_review_required, :validation_errors, :logged_at
            )
            """,
            record,
        )
        db_session.commit()
    except Exception as exc:
        logger.error("DB write failed for ai_usage_log: %s", exc)
        db_session.rollback()