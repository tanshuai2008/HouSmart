from app.services.census_service import CensusService


def validate_address(address: str):
    print(f"\nTesting: {address}")
    print("-" * 20)

    data = CensusService.get_income_by_address(address)

    if not data:
        print("No data found for this address.")
        return

    print("Tract GEOID:", data["tract_geoid"])
    print("State FIPS:", data["state_fips"])
    print("County Code:", data["county_code"])
    print("Tract Code:", data["tract_code"])

    income = data.get("median_income")

    # Handle income validation cases
    if income is None:
        print("Median Income: NOT AVAILABLE")
    elif income == -666666666:
        print("Median Income: SUPPRESSED BY CENSUS")
    elif income == 250001:
        print("Median Income: 250001+ (TOP-CODED BY CENSUS)")
    else:
        print("Median Income:", income)


if __name__ == "__main__":

    sample_addresses = [
        "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500",
        "350 5TH AVE, NEW YORK, NY 10118",
        "500 EAST FORDHAM RD, BRONX, NY 10458",
        "1 BEVERLY HILLS, CA 90210"
    ]

    for addr in sample_addresses:
        validate_address(addr)


# To Test: python -m app.tests.test_income_validation