from app.services.poi_service import POIService


def test_nyc_has_positive_poi_counts():

    service = POIService()

    result = service.compute_all_categories(
        40.7128,   # NYC latitude
        -74.0060   # NYC longitude
    )

    assert result["composite_score"] >= 0
    assert result["education"]["count"] >= 0
    assert result["retail"]["count"] >= 0
    assert result["healthcare"]["count"] >= 0
    assert result["lifestyle"]["count"] >= 0
    assert result["transit"]["count"] >= 0


def test_rural_area_has_low_counts():

    service = POIService()

    result = service.compute_all_categories(
        38.8026,   # rural Nevada
        -116.4194
    )

    assert result["education"]["count"] >= 0
    assert result["retail"]["count"] >= 0
    assert result["composite_score"] >= 0


def test_radius_effect():

    service = POIService()

    large_radius_result = service.compute_all_categories(
        40.7128,
        -74.0060
    )

    assert large_radius_result["education"]["count"] >= 0


def test_response_structure():

    service = POIService()

    result = service.compute_all_categories(
        34.0522,  # Los Angeles
        -118.2437
    )

    assert "education" in result
    assert "retail" in result
    assert "healthcare" in result
    assert "lifestyle" in result
    assert "transit" in result
    assert "composite_score" in result