import logging
import re

logger = logging.getLogger(__name__)

FORBIDDEN_WORDS = [
    "recommend", "guaranteed", "best", "perfect", "steal",
    "promising", "great deal", "must buy", "don't miss", "hot market", "sure thing",
]

MISSING_DATA_KEYWORDS: dict[str, list[str]] = {
    "crime_score":      ["crime", "safety", "criminal"],
    "school_score":     ["school", "education", "district"],
    "estimated_rent":   ["rent", "rental", "income", "yield", "roi"],
    "transit_score":    ["transit", "transportation", "commute"],
    "flood_risk_score": ["flood", "risk", "fema"],
    "amenity_score":    ["amenity", "amenities", "lifestyle"],
}

DISCLAIMER_TERMS = ["unavailable", "unknown", "manual verification", "missing", "not available"]


def validate_ai_output(ai_output: dict, deterministic_payload: dict) -> dict:
    errors:   list[str] = []
    warnings: list[str] = []
    ai_text = _extract_ai_text(ai_output)

    # Hard errors (Numerical hallucinations or bad confidence values)
    errors.extend(_check_numerical_integrity(ai_text, deterministic_payload))
    errors.extend(_check_confidence_pct(ai_output))
    
    # Soft warnings (Subjective language, missing disclaimers, or verdict disagreement)
    warnings.extend(_check_forbidden_words(ai_text))
    warnings.extend(_check_missing_data_disclaimers(ai_text, deterministic_payload))
    
    # Consistency is now a warning so the verdict explanation still shows up
    warnings.extend(_check_verdict_consistency(ai_output, deterministic_payload))

    # Flag for review ONLY if there are HARD errors. Warnings pass through to UI.
    admin_review_required = len(errors) > 0

    if errors:
        logger.warning("Validation failed for evaluation_id=%s — %d error(s): %s",
                       deterministic_payload.get("evaluation_id"), len(errors), errors)
    if warnings:
        logger.info("Validation warnings for evaluation_id=%s: %s",
                    deterministic_payload.get("evaluation_id"), warnings)

    ai_output["admin_review_required"] = admin_review_required
    ai_output["validation_errors"]     = errors
    ai_output["validation_warnings"]   = warnings

    if warnings:
        ai_output["subjective_language_warning"] = (
            "Note: This AI summary may contain subjective language or verdict disagreements. "
            "Please refer to the raw data metrics for final verification."
        )

    return ai_output


def _check_confidence_pct(ai_output: dict) -> list[str]:
    val = ai_output.get("ai_confidence_pct")
    if val is None:
        return []
    try:
        f = float(val)
        if not (0 <= f <= 100):
            return [f"ai_confidence_pct value {f} is out of range (must be 0-100)."]
    except (TypeError, ValueError):
        return [f"ai_confidence_pct is not a valid number: {val}"]
    return []


def _check_numerical_integrity(ai_text: str, payload: dict) -> list[str]:
    errors: list[str] = []
    ground_truth_floats: set[float] = set()

    # Combine financial and neighborhood metrics
    for val in {**payload.get("financial_metrics", {}), **payload.get("neighborhood_metrics", {})}.values():
        if val and isinstance(val, str) and "%" in val:
            match = re.search(r"(\d+\.?\d*)", val)
            if match:
                ground_truth_floats.add(float(match.group(1)))

    for val in payload.get("location_metrics", {}).values():
        if val is not None:
            try: ground_truth_floats.add(float(val))
            except (TypeError, ValueError): pass

    for val in payload.get("financial_metrics", {}).values():
        if val is not None and not isinstance(val, str):
            try: ground_truth_floats.add(float(val))
            except (TypeError, ValueError): pass

    # Check AI mentioned percentages against ground truth
    for pct_str in re.findall(r"(\d+\.?\d*)%", ai_text):
        try:
            pct_val = float(pct_str)
        except ValueError:
            continue
        if not any(abs(pct_val - ref) <= 0.6 for ref in ground_truth_floats):
            errors.append(f"AI mentioned {pct_str}% which does not match any ground-truth metric.")

    return errors


def _check_forbidden_words(ai_text: str) -> list[str]:
    lower = ai_text.lower()
    return [f"Subjective/forbidden word found: '{w}'" for w in FORBIDDEN_WORDS if w in lower]


def _check_missing_data_disclaimers(ai_text: str, payload: dict) -> list[str]:
    # We return these as warnings so the text is still visible
    warnings: list[str] = []
    lower_text = ai_text.lower()
    null_vars: set[str] = set(payload.get("failed_variables", []))
    
    for var, val in {**payload.get("location_metrics", {}), **payload.get("financial_metrics", {})}.items():
        if val is None:
            null_vars.add(var)

    for var_name in null_vars:
        keywords = MISSING_DATA_KEYWORDS.get(var_name, [])
        for kw in keywords:
            if kw not in lower_text:
                continue
            kw_index     = lower_text.find(kw)
            window_start = max(0, kw_index - 150)
            window_end   = min(len(lower_text), kw_index + 150)
            window       = lower_text[window_start:window_end]
            if not any(term in window for term in DISCLAIMER_TERMS):
                warnings.append(
                    f"AI referenced '{kw}' while '{var_name}' is null/failed without a disclaimer."
                )
            break
    return warnings


def _check_verdict_consistency(ai_output: dict, payload: dict) -> list[str]:
    """
    Checks if the AI narrative contradicts the payload color.
    Returns results as warnings to allow human review without breaking the UI.
    """
    warnings: list[str] = []
    verdict_color  = str(payload.get("verdict_color") or "").upper()
    ai_explanation = str(ai_output.get("verdict_explanation") or "").lower()

    if verdict_color == "RED":
        for s in ["strong investment", "excellent", "high return", "great opportunity"]:
            if s in ai_explanation:
                warnings.append(f"Consistency Warning: AI used positive phrase ('{s}') for a RED payload.")
                
    if verdict_color == "GREEN":
        for s in ["poor investment", "avoid", "significant risk", "not recommended"]:
            if s in ai_explanation:
                warnings.append(f"Consistency Warning: AI used negative phrase ('{s}') for a GREEN payload.")
                
    return warnings


def _extract_ai_text(ai_output: dict) -> str:
    parts: list[str] = []
    for key, val in ai_output.items():
        if key.startswith("_"): continue
        if isinstance(val, str): parts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str): parts.append(item)
                elif isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if isinstance(v, str))
    return " ".join(parts)
