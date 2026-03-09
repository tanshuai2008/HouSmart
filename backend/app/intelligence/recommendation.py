import json
import os
import re
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Model config
# LLM 1: cheaper + faster model for factual data interpretation
RECOMMENDATION_MODEL = os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.5-flash")
MAX_OUTPUT_TOKENS    = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))
TEMPERATURE          = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))  # low = consistent

#Prompt template path
_PROMPTS_DIR = Path(__file__).parent / "prompts"
_RECOMMENDATION_PROMPT_PATH = _PROMPTS_DIR / "recommendation_v1.txt"


def _load_system_prompt() -> str:
    """Load the recommendation system prompt from file."""
    try:
        return _RECOMMENDATION_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("recommendation_v1.txt not found at %s", _RECOMMENDATION_PROMPT_PATH)
        raise


def inject_policy(prompt: str, policy_summary: Optional[dict]) -> str:
    """
    Inject a formatted policy summary section into the recommendation prompt.
    Called only when the property is in a supported policy state (TX/WA/NC).

    Args:
        prompt:         The base user prompt string.
        policy_summary: Structured dict from policy.py, or None.

    Returns:
        The prompt string with a policy section appended.
    """
    if not policy_summary:
        return prompt

    state = policy_summary.get("state", "Unknown")
    summary_text = policy_summary.get("policy_summary", "")
    threats = policy_summary.get("threats", [])
    opportunities = policy_summary.get("opportunities", [])
    obligations = policy_summary.get("key_obligations", [])
    str_rules = policy_summary.get("str_restrictions", "")

    policy_block = f"""

## State Policy Context ({state})
The following regulatory information was retrieved from official policy documents.
Incorporate this into the investment_suitability and verdict_explanation sections where relevant.
Always cite the source when referencing a specific policy finding.

**Regulatory Summary:**
{summary_text}

**Key Threats:**
{_format_policy_items(threats)}

**Key Opportunities:**
{_format_policy_items(opportunities)}

**Key Obligations:**
{_format_policy_items(obligations)}

**Short-Term Rental Rules:**
{str_rules}

IMPORTANT: Reference only the above policy facts. Do not invent or assume any regulation not listed here.
"""

    return prompt + policy_block


def run_recommendation(
    payload: dict,
    policy_summary: Optional[dict] = None,
) -> dict:
    """
    Call Gemini Flash with the deterministic payload and optional policy context.
    Returns a validated structured JSON dict.

    Args:
        payload:        Deterministic JSON built by builder.py.
        policy_summary: Optional policy analysis from policy.py.

    Returns:
        Structured AI output dict matching the recommendation schema.

    Raises:
        ValueError:  If the model returns unparseable or invalid JSON.
        RuntimeError: If the Gemini API call fails.
    """
    system_prompt = _load_system_prompt()
    user_prompt   = _build_user_prompt(payload)
    user_prompt   = inject_policy(user_prompt, policy_summary)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

    logger.info(
        "Running recommendation LLM for evaluation_id=%s model=%s",
        payload.get("evaluation_id"), RECOMMENDATION_MODEL
    )

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model=RECOMMENDATION_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
            ),
        )
        raw_text = response.text

        # Store token usage metadata for logger
        usage = getattr(response, "usage_metadata", None)
        input_tokens  = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise RuntimeError(f"Recommendation LLM call failed: {exc}") from exc

    # Parse and validate
    parsed = _parse_json_response(raw_text)
    validated = _validate_schema(parsed)

    # Attach metadata for the logger
    validated["_meta"] = {
        "model":         RECOMMENDATION_MODEL,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "policy_injected": policy_summary is not None,
    }

    return validated


# Internal helpers

def _build_user_prompt(payload: dict) -> str:
    """
    Serialize the deterministic payload into the user-facing prompt section.
    """
    missing_flags_str = ""
    if payload.get("missing_data_flags"):
        missing_flags_str = "\n".join(payload["missing_data_flags"])
        missing_flags_str = f"\n\n## Missing Data Alerts\n{missing_flags_str}"

    priorities_str = ""
    if payload.get("user_priorities"):
        ranked = "\n".join(
            f"  {p['rank']}. {p['factor']}" for p in payload["user_priorities"]
        )
        priorities_str = f"\n\n## User Priority Ranking (1 = most important)\n{ranked}"

    prompt = f"""## Property Evaluation Data

Verdict Color: **{payload.get('verdict_color', 'UNKNOWN')}**

Property:
{json.dumps(payload.get('property', {}), indent=2)}

Financial Metrics:
{json.dumps(payload.get('financial_metrics', {}), indent=2)}

Location Intelligence:
{json.dumps(payload.get('location_metrics', {}), indent=2)}

Neighborhood Metrics:
{json.dumps(payload.get('neighborhood_metrics', {}), indent=2)}

Data Completeness: {payload.get('data_completeness_pct', 0)}%
{priorities_str}{missing_flags_str}

Generate the investment analysis JSON as instructed."""

    return prompt


def _parse_json_response(raw_text: str) -> dict:
    """
    Parse JSON from the model response, stripping any accidental markdown fences.
    """
    # Strip markdown code fences if present despite response_mime_type enforcement
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().rstrip("```").strip()

    # Detect truncation early — a complete JSON object must end with "}"
    if not cleaned.rstrip().endswith("}"):
        logger.error(
            "AI response appears truncated (does not end with '}'). "
            "Increase GEMINI_MAX_TOKENS. Last 100 chars: ...%s", cleaned[-100:]
        )
        raise ValueError(
            "AI response was truncated mid-JSON. Increase GEMINI_MAX_TOKENS "
            f"(currently {MAX_OUTPUT_TOKENS}). Last 100 chars: ...{cleaned[-100:]}"
        )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI response as JSON: %s\nRaw: %s", exc, raw_text[:500])
        raise ValueError(f"AI returned invalid JSON: {exc}") from exc


def _validate_schema(data: dict) -> dict:
    """
    Ensure the required keys are present in the AI response.
    Fill missing optional fields with null rather than failing hard.
    """
    required_keys = [
        "community_profile",
        "safety_and_amenities",
        "investment_suitability",
        "verdict_explanation",
        "key_strengths",
        "key_risks",
    ]
    optional_keys = ["missing_data_note", "policy_highlights"]

    for key in required_keys:
        if key not in data:
            logger.warning("AI response missing required key: %s — filling with null", key)
            data[key] = None

    for key in optional_keys:
        if key not in data:
            data[key] = None

    return data


def _format_policy_items(items: list) -> str:
    """Format a list of policy findings for prompt injection."""
    if not items:
        return "None found in retrieved documents."
    return "\n".join(
        f"- {item.get('finding', '')} (Source: {item.get('source', 'Unknown')})"
        for item in items
    )