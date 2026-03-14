import requests
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def get_zip_from_address(address: str):

    url = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": address,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    if not data["results"]:
        return None

    components = data["results"][0]["address_components"]

    for comp in components:
        if "postal_code" in comp["types"]:
            return comp["long_name"]

    return None