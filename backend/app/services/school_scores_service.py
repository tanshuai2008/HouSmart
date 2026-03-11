import re
import logging
import requests

from app.services.supabase_client import get_supabase
from app.core.config import settings


logger = logging.getLogger(__name__)


class SchoolScoreServiceError(Exception):
    pass


def _get_zip_from_google(address: str) -> str | None:
    """Helper to extract ZIP code using Google Maps Geocoding API."""
    if not settings.GOOGLE_MAPS_API_KEY:
        return None

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": settings.GOOGLE_MAPS_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return None

        components = data["results"][0].get("address_components", [])
        for comp in components:
            if "postal_code" in comp.get("types", []):
                return comp.get("long_name")
    except Exception as exc:
        logger.warning("Google Geocoding ZIP extraction failed: %s", exc)
    return None


def _fetch_schools_by_zip(supabase, zip_code: str) -> list:
    """
    Helper to query school_master for schools in the district associated with a ZIP.
    Follows ah/housmart logic: ZIP -> District -> All Schools in District.
    """
    try:
        # 1. Find the district_id for this ZIP
        district_resp = (
            supabase.table("school_master")
            .select("district_id")
            .eq("zip_code", zip_code)
            .limit(1)
            .execute()
        )
        
        if not district_resp.data:
            return []
            
        district_id = district_resp.data[0].get("district_id")
        if not district_id:
            return []

        # 2. Fetch schools in that district that actually have a score
        resp = (
            supabase.table("school_master")
            .select("school_name, level, housmart_school_score, s_academic, s_resource, s_equity, academic_percentile, growth_percentile, math_percentile, score_fields_used, score_fields_missing")
            .eq("district_id", district_id)
            .not_.is_("housmart_school_score", "null")
            .order("housmart_school_score", desc=True)
            .limit(10)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        logger.error("Error fetching schools for District/ZIP %s: %s", zip_code, exc)
        return []


def fetch_school_scores(address: str) -> dict:
    normalized_address = address.strip()
    if not normalized_address:
        raise ValueError("Address is required")

    try:
        supabase = get_supabase()
        schools = []
        search_type = "zip_code"
        search_value = "unknown"

        # 1. ZIP extraction
        zip_code = None
        # Try regex first (fast)
        zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", normalized_address)
        if zip_match:
            zip_code = zip_match.group(1)
        else:
            # Try Google fallback (more accurate)
            zip_code = _get_zip_from_google(normalized_address)

        if zip_code:
            search_type = "zip_code"
            search_value = zip_code
            
            # Check exact match
            schools = _fetch_schools_by_zip(supabase, zip_code)
            
            # Check without leading zero (handles data ingestion issues for East Coast ZIPs)
            if not schools and zip_code.startswith("0"):
                schools = _fetch_schools_by_zip(supabase, zip_code.lstrip("0"))

            # 3. If still no schools, try nearby ZIP codes (±1, ±2)
            if not schools:
                try:
                    base_zip = int(zip_code)
                    nearby_zips = [
                        base_zip + 1,
                        base_zip - 1,
                        base_zip + 2,
                        base_zip - 2,
                    ]
                    for z in nearby_zips:
                        z_str = str(z).zfill(5)
                        z_stripped = str(z)
                        
                        schools = _fetch_schools_by_zip(supabase, z_str)
                        if not schools and z_str.startswith("0"):
                            schools = _fetch_schools_by_zip(supabase, z_stripped)
                            
                        if schools:
                            search_value = z_str
                            break
                except (ValueError, TypeError):
                    pass

        if not schools:
            return {
                "search_type": search_type,
                "search_value": search_value,
                "message": f"No schools found for {search_type}: {search_value}",
                "total_schools_found": 0,
                "schools": [],
            }

        # 4. Calculate aggregated property school score
        # Logic: Only consider schools with a valid housmart_school_score, s_academic, and in specific levels.
        property_school_score = None
        if schools:
            valid_scores = [
                s.get("housmart_school_score")
                for s in schools
                if s.get("housmart_school_score") is not None
                and s.get("s_academic") is not None
                and s.get("level") in ["Elementary", "Middle", "High"]
            ]
            if valid_scores:
                property_school_score = round(sum(valid_scores) / len(valid_scores), 1)

        return {
            "search_type": search_type,
            "search_value": search_value,
            "property_school_score": property_school_score,
            "total_schools_found": len(schools),
            "schools": schools,
        }
    except ValueError:
        raise
    except Exception as exc:
        raise SchoolScoreServiceError(f"Database query failed: {exc}") from exc