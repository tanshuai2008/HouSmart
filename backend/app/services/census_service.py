import requests

class CensusService:

    BASE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
    
    @staticmethod
    def get_location_data(address: str):
        params = {
            "address": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }

        response = requests.get(CensusService.BASE_URL, params=params)
        data = response.json()

        if not data["result"]["addressMatches"]:
            return None

        match = data["result"]["addressMatches"][0]
        components = match["addressComponents"]


        tract_geoid = match["geographies"]["Census Tracts"][0]["GEOID"]

        return {
            "formatted_address": match["matchedAddress"],
            "street": components.get("street"),
            "city": components.get("city"),
            "state": components.get("state"),
            "zip_code": components.get("zip"),
            "county_fips": match["geographies"]["Counties"][0]["GEOID"],
            "tract_geoid": tract_geoid,  
            "latitude": match["coordinates"]["y"],
            "longitude": match["coordinates"]["x"]
        }