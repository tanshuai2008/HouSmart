import json
import os
import re
import logging
from pathlib import Path
from typing import Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger(__name__)

RECOMMENDATION_MODEL = os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.5-flash")
MAX_OUTPUT_TOKENS    = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))
TEMPERATURE          = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_RECOMMENDATION_PROMPT_PATH = _PROMPTS_DIR / "recommendation_v2.txt"


def _load_system_prompt() -> str:
    try:
        return _RECOMMENDATION_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("recommendation_v1.txt not found at %s", _RECOMMENDATION_PROMPT_PATH)
        raise


def inject_policy(prompt: str, policy_summary: Optional[dict]) -> str:
    if not policy_summary:
        return prompt

    state         = policy_summary.get("state", "Unknown")
    summary_text  = policy_summary.get("policy_summary", "")
    threats       = policy_summary.get("threats", [])
    opportunities = policy_summary.get("opportunities", [])
    obligations   = policy_summary.get("key_obligations", [])
    str_rules     = policy_summary.get("str_restrictions", "")

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
    system_prompt = _load_system_prompt()
    user_prompt   = _build_user_prompt(payload)
    user_prompt   = inject_policy(user_prompt, policy_summary)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
    if genai is None or types is None:
        raise ImportError(
            "google-genai is not installed in the active backend environment. "
            "Install dependencies from backend/requirements.txt."
        )

    logger.info(
        "Running recommendation LLM for evaluation_id=%s model=%s",
        payload.get("evaluation_id"), RECOMMENDATION_MODEL
    )

    try:
        client = genai.Client(api_key=api_key)
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

        usage         = getattr(response, "usage_metadata", None)
        input_tokens  = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise RuntimeError(f"Recommendation LLM call failed: {exc}") from exc

    parsed    = _parse_json_response(raw_text)
    validated = _validate_schema(parsed)

    validated["_meta"] = {
        "model":           RECOMMENDATION_MODEL,
        "input_tokens":    input_tokens,
        "output_tokens":   output_tokens,
        "policy_injected": policy_summary is not None,
    }

    return validated


def _build_user_prompt(payload: dict) -> str:
    missing_flags_str = ""
    if payload.get("missing_data_flags"):
        missing_flags_str = "\n".join(payload["missing_data_flags"])
        missing_flags_str = f"\n\n## Missing Data Alerts\n{missing_flags_str}"

    profile_str    = _format_user_profile_block(payload.get("user_profile", {}))

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
{profile_str}{priorities_str}{missing_flags_str}

Generate the investment analysis JSON as instructed."""

    return prompt


def _format_user_profile_block(user_profile: dict) -> str:
    if not user_profile:
        return ""

    experience   = user_profile.get("experience_level", "") or ""
    primary_role = user_profile.get("primary_role", "") or ""
    goal         = user_profile.get("investment_goal", "") or ""
    priorities   = user_profile.get("priorities_ranking", [])

    is_newbie = "newbie" in experience.lower()

    tone_note = (
        "This investor is new to real estate. Use clear, jargon-free language. "
        "Explain key metrics briefly where relevant."
        if is_newbie else
        "This investor is experienced. Use precise financial language and avoid over-explaining basics."
    )

    priorities_str = _format_priority_values(priorities)

    return f"""

## Investor Profile
- Role: {primary_role or 'not specified'}
- Experience: {experience or 'not specified'}
- Investment Goal: {goal or 'not specified'}
- What they care about most: {priorities_str}

Tone guidance: {tone_note}
Tailor the headline, summary_blurb, and verdict_explanation to reflect this investor's goal and priorities."""


def _format_priority_values(priorities) -> str:
    if not priorities:
        return "not specified"
    if not isinstance(priorities, list):
        return str(priorities)

    formatted = []
    for item in priorities:
        if isinstance(item, str):
            formatted.append(item)
            continue
        if isinstance(item, dict):
            factor = item.get("factor") or item.get("label") or item.get("name")
            rank = item.get("rank")
            if factor and rank is not None:
                formatted.append(f"{rank}. {factor}")
            elif factor:
                formatted.append(str(factor))
            continue
        formatted.append(str(item))

    return ", ".join(formatted) if formatted else "not specified"


def _parse_json_response(raw_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?|```", "", raw_text).strip()

    if not cleaned.rstrip().endswith("}"):
        logger.error("AI response appears truncated. Last 100 chars: ...%s", cleaned[-100:])
        raise ValueError(
            f"AI response was truncated mid-JSON. Increase GEMINI_MAX_TOKENS "
            f"(currently {MAX_OUTPUT_TOKENS}). Last 100 chars: ...{cleaned[-100:]}"
        )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI response as JSON: %s\nRaw: %s", exc, raw_text[:500])
        raise ValueError(f"AI returned invalid JSON: {exc}") from exc


def _validate_schema(data: dict) -> dict:
    required_keys = [
        "verdict_label",
        "ai_confidence_pct",
        "headline",
        "summary_blurb",
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
    if not items:
        return "None found in retrieved documents."
    return "\n".join(
        f"- {item.get('finding', '')} (Source: {item.get('source', 'Unknown')})"
        for item in items
    )
