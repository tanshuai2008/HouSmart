# HouSmart/backend/app/tests/test_education_validation.py
import requests
import pytest
from app.core.config import settings
from app.core.supabase_client import supabase


ACS_URL = "https://api.census.gov/data/2024/acs/acs5"


def validate_education_metric(tract_geoid: str):

    state = tract_geoid[:2]
    county = tract_geoid[2:5]
    tract = tract_geoid[5:]

    params = {
        "get": "B15003_001E,B15003_022E",
        "for": f"tract:{tract}",
        "in": f"state:{state}+county:{county}",
        "key": settings.CENSUS_API_KEY
    }

    response = requests.get(ACS_URL, params=params)
    response.raise_for_status()

    data = response.json()

    total = float(data[1][0])
    bachelor = float(data[1][1])

    computed_pct = round((bachelor / total) * 100, 2)

    db_result = (
        supabase
        .table("geo_tract_metrics")
        .select("education_bachelor_pct")
        .eq("tract_geoid", tract_geoid)
        .execute()
    )

    if not db_result.data:
        return {"error": "Tract not found in database"}

    stored_pct = db_result.data[0]["education_bachelor_pct"]

    return {
        "computed_pct": computed_pct,
        "stored_pct": stored_pct,
        "match": computed_pct == stored_pct
    }


# TEST 
@pytest.mark.parametrize("tract_geoid", [
    "36061007600",
    "36061012200",
])

def test_validate_education_metric(tract_geoid):

    result = validate_education_metric(tract_geoid)

    assert "computed_pct" in result
    assert "stored_pct" in result
    assert result["match"] is True


if __name__ == "__main__":
    sample_tracts = [
        "36061007600",  # 350 5TH AVE, NEW YORK, NY
        "36061012200",  # NEW YORK
        "34039035100",  # 1 N WOOD AVE, LINDEN, NJ
        "11001980000",  # 1600 PENNSYLVANIA AVE, WASHINGTON DC
    ]

    for tract in sample_tracts:
        print(f"\nTesting tract: {tract}")
        print("-" * 20)
        result = validate_education_metric(tract)
        print(result)
