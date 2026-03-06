from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict


class AgencyMetadata(TypedDict):
    ori: str
    name: str
    type: str


class ORIMetadataResult(TypedDict):
    normalized_address: str
    place_fips: Optional[str]
    county_fips: Optional[str]
    census_population: Optional[int]
    agency: AgencyMetadata
    crime_offense_codes: Dict[str, str]
    crime_weights: Dict[str, float]


@dataclass
class GeocodedLocation:
    normalized_address: str
    place_fips: Optional[str]
    county_fips: Optional[str]
    census_population: Optional[int]


@dataclass
class CrosswalkRecord:
    ori: str
    agency_name: str
    agency_type: str


class CrimeCategoryBreakdown(TypedDict):
    alias: str
    offense_code: str
    weight: float
    local_rate_per_100k: float
    national_rate_per_100k: float
    rate_ratio: float
    months_with_data: int
    weighted_local_rate: float
    weighted_national_rate: float


class CrimeSafetyScoreResult(TypedDict):
    normalized_address: str
    agency: AgencyMetadata
    date_range: Dict[str, str]
    months_analyzed: int
    local_crime_index: float
    national_crime_index: float
    relative_crime_ratio: float
    safety_score: float
    safety_category: str
    offense_breakdown: List[CrimeCategoryBreakdown]
    data_available: bool
    message: Optional[str]
