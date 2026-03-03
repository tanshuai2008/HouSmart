import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class OSMFetchService:

    def fetch_all_pois(self, latitude, longitude, radius_meters):

        query = f"""
        [out:json][timeout:60];
        (
          node(around:{radius_meters},{latitude},{longitude})["amenity"~"school|college|university|library|hospital|clinic|dentist"];
          node(around:{radius_meters},{latitude},{longitude})["shop"~"supermarket|mall"];
          node(around:{radius_meters},{latitude},{longitude})["leisure"~"park"];
          node(around:{radius_meters},{latitude},{longitude})["railway"~"station"];
        );
        out body;
        """

        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=60
        )

        if response.status_code != 200:
            print("Overpass error:", response.status_code)
            return []

        return response.json().get("elements", [])