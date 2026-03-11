# HouSmart/backend/app/services/census_service.py
import requests
from app.core.config import settings
from app.core.supabase_client import supabase


class CensusService:

    GEOCODER_URL  = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
    ACS_URL = "https://api.census.gov/data/2024/acs/acs5"

    @staticmethod
    def get_location_data(address: str):
        params = {
            "address": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }

        response = requests.get(CensusService.GEOCODER_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if not data["result"]["addressMatches"]:
            return None

        match = data["result"]["addressMatches"][0]
        components = match["addressComponents"]

        tract = match["geographies"]["Census Tracts"][0]
        county = match["geographies"]["Counties"][0]

        return {
            "formatted_address": match["matchedAddress"],
            "street": components.get("street"),
            "city": components.get("city"),
            "state": components.get("state"),
            "zip_code": components.get("zip"),
            "county_fips": county["GEOID"],
            "tract_geoid": tract["GEOID"],
            "state_fips": tract["STATE"],
            "county_code": tract["COUNTY"],
            "tract_code": tract["TRACT"],
            "latitude": match["coordinates"]["y"],
            "longitude": match["coordinates"]["x"]
        }

    @staticmethod
    def _get_cached_tract_metrics(tract_geoid: str):
        if not tract_geoid:
            return None
        try:
            response = (
                supabase.table("geo_tract_metrics")
                .select("median_income, education_bachelor_pct")
                .eq("tract_geoid", tract_geoid)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            return rows[0] if rows else None
        except Exception:
            return None

    @staticmethod
    def _upsert_cached_tract_metrics(
        *,
        location_data: dict,
        median_income: int | None = None,
        education_bachelor_pct: float | None = None,
    ):
        tract_geoid = location_data.get("tract_geoid")
        if not tract_geoid:
            return
        payload = {
            "tract_geoid": tract_geoid,
            "state_fips": location_data.get("state_fips"),
            "county_fips": location_data.get("county_code"),
        }
        if median_income is not None:
            payload["median_income"] = median_income
        if education_bachelor_pct is not None:
            payload["education_bachelor_pct"] = education_bachelor_pct
        try:
            supabase.table("geo_tract_metrics").upsert(payload).execute()
        except Exception:
            return
    
    @staticmethod
    def get_median_income(state: str, county: str, tract: str):
        params = {
            "get" : "B19013_001E",
            "for": f"tract:{tract}",
            "in": f"state:{state}+county:{county}",
            "key": settings.CENSUS_API_KEY
        }

        response = requests.get(CensusService.ACS_URL, params=params)
        response.raise_for_status()

        data = response.json()

        return int(data[1][0])
    
    @staticmethod
    def get_income_by_address(address: str):
        location_data = CensusService.get_location_data(address)
        if not location_data:
            return None

        cached = CensusService._get_cached_tract_metrics(location_data.get("tract_geoid"))
        cached_income = None if not cached else cached.get("median_income")
        if cached_income is not None:
            location_data['median_income'] = int(cached_income)
            location_data["api_used"] = "cache"
            location_data["source"] = "geo_tract_metrics"
            return location_data

        income = CensusService.get_median_income(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )
        CensusService._upsert_cached_tract_metrics(
            location_data=location_data,
            median_income=income,
        )

        location_data['median_income'] = income
        location_data["api_used"] = "census_api"
        location_data["source"] = "US Census ACS 2024"
        
        return location_data
    
    @staticmethod
    def get_bachelor_percentage(state: str, county: str, tract: str):
        params = {
            "get": "B15003_001E,B15003_022E",
            "for": f"tract:{tract}",
            "in": f"state:{state}+county:{county}",
            "key": settings.CENSUS_API_KEY
        }

        response = requests.get(
            CensusService.ACS_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        total_20_plus = float(data[1][0])
        bachelor_count = float(data[1][1])

        if total_20_plus == 0:
            return None
        bachelor_percentage = (bachelor_count / total_20_plus) * 100

        return round(bachelor_percentage, 2)
    

    @staticmethod
    def get_education_by_address(address: str):
        location_data = CensusService.get_location_data(address=address)
        if not location_data:
            return None

        cached = CensusService._get_cached_tract_metrics(location_data.get("tract_geoid"))
        cached_education = None if not cached else cached.get("education_bachelor_pct")
        if cached_education is not None:
            location_data['bachelor_percentage'] = float(cached_education)
            location_data["api_used"] = "cache"
            location_data["source"] = "geo_tract_metrics"
            return location_data

        education_percentage = CensusService.get_bachelor_percentage(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )
        CensusService._upsert_cached_tract_metrics(
            location_data=location_data,
            education_bachelor_pct=education_percentage,
        )

        location_data['bachelor_percentage'] = education_percentage
        location_data["api_used"] = "census_api"
        location_data["source"] = "US Census ACS 2024"

        return location_data

    
    
    @staticmethod
    def get_income_and_education_by_address(address: str):
        location_data = CensusService.get_location_data(address)
        if not location_data:
            return None

        income = CensusService.get_median_income(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )

        bachelor_pct = CensusService.get_bachelor_percentage(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )

        location_data["median_income"] = income
        location_data["bachelor_percentage"] = bachelor_pct

        return location_data
