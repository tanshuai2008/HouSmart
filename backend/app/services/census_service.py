# HouSmart/backend/app/services/census_service.py
import requests
from app.core.config import settings

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

        income = CensusService.get_median_income(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )

        location_data['median_income'] = income
        
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

        education_percentage = CensusService.get_bachelor_percentage(
            state=location_data["state_fips"],
            county=location_data["county_code"],
            tract=location_data["tract_code"]
        )

        location_data['bachelor_percentage'] = education_percentage

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
