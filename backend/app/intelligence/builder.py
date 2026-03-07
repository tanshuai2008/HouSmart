from typing import Optional


# Variables that are REQUIRED for a valid evaluation.
# If all of these are either ready or failed, the AI can proceed.
REQUIRED_VARIABLES = [
    "estimated_rent",
    "crime_score",
    "school_score",
    "transit_score",
    "flood_risk_score",
    "amenity_score",
    "noise_score",
    "median_income",
    "median_home_value",
    "vacancy_rate",
]


def build_base_payload(
    evaluation_data: dict,
    priority_ranking: Optional[list] = None,
) -> dict:
    """
    Build the deterministic JSON payload for the AI engine.

    Args:
        evaluation_data: Dict containing:
            - evaluation_id
            - property (address, lat, lng, state, bedrooms, etc.)
            - variables: { variable_name: { status, value, source, ... } }
            - financials: { cap_rate, cash_flow, roi_5yr, estimated_value }
            - verdict_color: "green" | "yellow" | "red"
        priority_ranking: List of user priority dicts from user_onboarding_profiles.
            e.g. [{"factor": "roi", "rank": 1}, {"factor": "safety", "rank": 2}, ...]

    Returns:
        Structured deterministic payload dict ready for the AI prompt.
    """
    variables = evaluation_data.get("variables", {})
    property_info = evaluation_data.get("property", {})
    financials = evaluation_data.get("financials", {})
    verdict_color = evaluation_data.get("verdict_color", "yellow").upper()

    #1. Separate ready vs failed variables
    ready_vars: dict = {}
    failed_vars: list = []
    missing_data_flags: list = []

    for var_name in REQUIRED_VARIABLES:
        var_data = variables.get(var_name, {})
        status = var_data.get("status", "pending")

        if status == "ready":
            ready_vars[var_name] = {
                "value": var_data.get("value"),
                "source": var_data.get("source", "Unknown"),
                "fetched_at": var_data.get("fetched_at"),
            }
        elif status == "failed":
            failed_vars.append(var_name)
            missing_data_flags.append(
                f"Note: '{var_name}' data is unavailable. "
                f"Adjust your analysis to be cautious and advise manual verification."
            )
        # pending variables are ignored — orchestrator ensures all are settled first

    #2. Build financial metrics block
    financial_metrics = {
        "monthly_cash_flow":    financials.get("monthly_cash_flow"),
        "cap_rate_pct":         _fmt_pct(financials.get("cap_rate")),
        "roi_5yr_pct":          _fmt_pct(financials.get("roi_5yr")),
        "estimated_value":      financials.get("estimated_value"),
        "estimated_rent":       ready_vars.get("estimated_rent", {}).get("value"),
    }

    #3. Build location intelligence block
    location_metrics = {
        "crime_score":          _get_val(ready_vars, "crime_score"),
        "school_score":         _get_val(ready_vars, "school_score"),
        "transit_score":        _get_val(ready_vars, "transit_score"),
        "flood_risk_score":     _get_val(ready_vars, "flood_risk_score"),
        "amenity_score":        _get_val(ready_vars, "amenity_score"),
        "noise_score":          _get_val(ready_vars, "noise_score"),
    }

    #4. Build census/neighborhood block
    neighborhood_metrics = {
        "median_income":        _get_val(ready_vars, "median_income"),
        "median_home_value":    _get_val(ready_vars, "median_home_value"),
        "vacancy_rate_pct":     _fmt_pct(_get_val(ready_vars, "vacancy_rate")),
        "education_bachelor_pct": _get_val(ready_vars, "education_bachelor_pct"),
    }

    #5. Format priority ranking
    formatted_priorities = _format_priorities(priority_ranking)

    #6. Assemble final payload
    payload = {
        "evaluation_id":    evaluation_data.get("evaluation_id"),
        "verdict_color":    verdict_color,
        "property": {
            "address":          property_info.get("formatted_address"),
            "state":            property_info.get("state"),
            "zip_code":         property_info.get("zip_code"),
            "bedrooms":         property_info.get("bedrooms"),
            "bathrooms":        property_info.get("bathrooms"),
            "square_feet":      property_info.get("square_feet"),
            "year_built":       property_info.get("year_built"),
            "property_type":    property_info.get("property_type"),
        },
        "financial_metrics":        financial_metrics,
        "location_metrics":         location_metrics,
        "neighborhood_metrics":     neighborhood_metrics,
        "user_priorities":          formatted_priorities,
        "failed_variables":         failed_vars,
        "missing_data_flags":       missing_data_flags,
        "data_completeness_pct":    _compute_completeness(ready_vars),
    }

    return payload


#Helpers

def _get_val(ready_vars: dict, key: str):
    """Return the value for a ready variable, or None if missing."""
    entry = ready_vars.get(key)
    return entry["value"] if entry else None


def _fmt_pct(value) -> Optional[str]:
    """Format a decimal ratio as a percentage string, or None."""
    if value is None:
        return None
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return None


def _format_priorities(priority_ranking: Optional[list]) -> list:
    """
    Normalize the user's priority ranking into a clean list sorted by rank.
    """
    if not priority_ranking:
        return []
    try:
        sorted_priorities = sorted(priority_ranking, key=lambda x: x.get("rank", 99))
        return [
            {"rank": idx + 1, "factor": p.get("factor", "unknown")}
            for idx, p in enumerate(sorted_priorities)
        ]
    except Exception:
        return []


def _compute_completeness(ready_vars: dict) -> float:
    """Return percentage of required variables that are ready (0–100)."""
    if not REQUIRED_VARIABLES:
        return 100.0
    ready_count = sum(1 for v in REQUIRED_VARIABLES if v in ready_vars)
    return round((ready_count / len(REQUIRED_VARIABLES)) * 100, 1)