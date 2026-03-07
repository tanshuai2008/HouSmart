from typing import Dict, List, Any
from datetime import datetime, timezone


FAILED_NOTE_TEMPLATE = (
    "{variable} data could not be retrieved from external sources. "
    "AI should acknowledge the missing data and respond cautiously."
)

VALID_STATUS = {"ready", "pending", "failed"}


def _build_variable_block(variable: Dict[str, Any]) -> Dict[str, Any]:

    name = variable.get("name")
    value = variable.get("value")
    status = variable.get("status", "pending")

    if status not in VALID_STATUS:
        status = "pending"

    block = {
        "value": value,
        "status": status
    }

    if status == "failed":
        block["note"] = FAILED_NOTE_TEMPLATE.format(variable=name)

    return block


def _normalize_variables(variable_rows: List[Dict[str, Any]]) -> Dict[str, Dict]:

    variables = {}

    if not isinstance(variable_rows, list):
        return variables

    for row in variable_rows:

        if not isinstance(row, dict):
            continue

        name = row.get("name")

        if not name:
            continue

        variables[name] = _build_variable_block(row)

    variables = dict(sorted(variables.items()))

    return variables


def _build_metadata(evaluation_data: Dict) -> Dict:

    return {
        "evaluation_id": evaluation_data.get("evaluation_id"),
        "state": evaluation_data.get("state"),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def _build_data_quality_summary(variables: Dict[str, Dict]) -> Dict:

    ready = 0
    failed = 0
    pending = 0

    for var in variables.values():

        status = var.get("status")

        if status == "ready":
            ready += 1
        elif status == "failed":
            failed += 1
        else:
            pending += 1

    return {
        "ready_variables": ready,
        "failed_variables": failed,
        "pending_variables": pending
    }


def build_base_payload(evaluation_data: Dict) -> Dict:

    if not isinstance(evaluation_data, dict):
        evaluation_data = {}

    variable_rows = evaluation_data.get("variables", [])

    priority_ranking = evaluation_data.get("priority_ranking", [])

    if not isinstance(priority_ranking, list):
        priority_ranking = []

    variables = _normalize_variables(variable_rows)

    payload = {
        "metadata": _build_metadata(evaluation_data),
        "priority_ranking": priority_ranking,
        "variables": variables,
        "data_quality": _build_data_quality_summary(variables)
    }

    return payload


if __name__ == "__main__":

    example_input = {
        "evaluation_id": "EV12345",
        "state": "Texas",
        "priority_ranking": [
            "school_quality",
            "safety",
            "flood_risk"
        ],
        "variables": [
            {"name": "school_rating", "value": 8.4, "status": "ready"},
            {"name": "crime_rate", "value": 0.31, "status": "ready"},
            {"name": "flood_risk", "value": None, "status": "failed"},
            {"name": "walkability_score", "value": None, "status": "pending"},
            {"value": 5.2, "status": "ready"},  
            {"name": "invalid_status", "value": 1, "status": "error"}
        ]
    }

    result = build_base_payload(example_input)

    import json
    print(json.dumps(result, indent=2))
