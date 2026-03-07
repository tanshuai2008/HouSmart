import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Approximate cost per 1M tokens (USD)
COST_PER_1M_INPUT_TOKENS: dict[str, float] = {
    "gemini-2.5-flash":   0.075,   # input
    "gemini-2.0-flash":   0.075,   # input
    "gemini-1.5-flash":   0.075,   # input
    "gemini-1.5-pro":     1.25,    # input
}
COST_PER_1M_OUTPUT_TOKENS: dict[str, float] = {
    "gemini-2.5-flash":   0.30,
    "gemini-2.0-flash":   0.30,
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
        db_session:     Supabase client for writing to ai_usage_logs table.
    """
    try:
        # ── Extract recommendation model usage ────────────────────────────
        rec_meta       = result.get("_meta", {})
        input_tokens   = rec_meta.get("input_tokens", 0)
        output_tokens  = rec_meta.get("output_tokens", 0)
        total_tokens   = input_tokens + output_tokens
        rec_model      = rec_meta.get("model", model_used)
        policy_ran     = bool((policy_summary or {}).get("_meta"))

        # ── Compute cost ───────────────────────────────────────────────────
        cost = _compute_cost(rec_model, input_tokens, output_tokens)

        # ── Also add policy model cost if ran ─────────────────────────────
        pol_meta = (policy_summary or {}).get("_meta", {})
        if pol_meta:
            cost += _compute_cost(
                pol_meta.get("model"),
                pol_meta.get("input_tokens", 0),
                pol_meta.get("output_tokens", 0),
            )
            total_tokens += pol_meta.get("input_tokens", 0) + pol_meta.get("output_tokens", 0)

        record = {
            "evaluation_id":      evaluation_id,
            "model_used":         rec_model,
            "prompt_version":     "recommendation_v1",
            "prompt_tokens":      input_tokens,
            "completion_tokens":  output_tokens,
            "total_tokens":       total_tokens,
            "estimated_cost_usd": round(cost, 6),
            "recommendation":     result.get("verdict_color"),
            "confidence_score":   result.get("data_completeness_pct"),
            "policy_used":        policy_ran,
        }

        # ── Write to Supabase ──────────────────────────────────────────────
        if db_session:
            db_session.table("ai_usage_logs").insert(record).execute()
            logger.info("AI usage logged — evaluation_id=%s cost=$%s",
                        evaluation_id, record["estimated_cost_usd"])
        else:
            # Dev fallback: log to console
            logger.info("AI Usage [evaluation_id=%s]: %s", evaluation_id, record)

    except Exception as exc:
        # Never let logging failure break the response
        logger.error("Failed to log AI usage for evaluation_id=%s: %s", evaluation_id, exc)


def _compute_cost(model: Optional[str], input_tokens: int, output_tokens: int) -> float:
    if not model:
        return 0.0
    # Gemini returns full path e.g. "models/gemini-2.5-flash" — strip the prefix
    model = model.replace("models/", "")
    input_cost  = (input_tokens  / 1_000_000) * COST_PER_1M_INPUT_TOKENS.get(model, 0.0)
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS.get(model, 0.0)
    return input_cost + output_cost
