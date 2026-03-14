## Test 1: test_nyc_has_positive_poi_counts

Validates:

* Engine returns structured result

* Counts are numeric

* Composite score calculated

## Test 2: test_rural_area_has_low_counts

Validates:

* System works in low-density areas

* No crash when POIs are sparse

## Test 3: test_radius_effect

Validates:

* Radius queries return data

* PostGIS function works

## Test 4: test_response_structure

Validates:

* API result format is correct

* All scoring categories exist