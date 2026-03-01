import unittest
from unittest.mock import patch


class TestNoiseEstimator(unittest.TestCase):
    def test_distance_to_noise_buckets(self):
        from app.services.noise_estimator import _distance_to_noise

        self.assertEqual(_distance_to_noise(0), "Very High")
        self.assertEqual(_distance_to_noise(19.999), "Very High")
        self.assertEqual(_distance_to_noise(20), "High")
        self.assertEqual(_distance_to_noise(49.999), "High")
        self.assertEqual(_distance_to_noise(50), "Moderate")
        self.assertEqual(_distance_to_noise(149.999), "Moderate")
        self.assertEqual(_distance_to_noise(150), "Low")

    @patch("app.services.noise_estimator.get_cached", autospec=True)
    @patch("app.services.noise_estimator._compute_noise_factors", autospec=True)
    def test_estimate_noise_returns_cached(self, mock_compute_noise_factors, mock_get_cached):
        from app.services.noise_estimator import estimate_noise

        cached = {"noise_level": "Low", "distance_to_road_m": 999}
        mock_get_cached.return_value = cached

        out = estimate_noise(10.123456, 20.654321)

        self.assertEqual(out, cached)
        mock_compute_noise_factors.assert_not_called()

    @patch("app.services.noise_estimator.set_cache", autospec=True)
    @patch("app.services.noise_estimator.get_cached", autospec=True)
    @patch("app.services.noise_estimator._compute_noise_factors", autospec=True)
    def test_estimate_noise_sets_cache_and_returns_result(
        self,
        mock_compute_noise_factors,
        mock_get_cached,
        mock_set_cache,
    ):
        from app.services.noise_estimator import estimate_noise

        mock_get_cached.return_value = None

        # Provide deterministic factors (avoid network). Values chosen to yield a high score.
        mock_compute_noise_factors.return_value = {
            "roads": {
                "radius_m": 600,
                "road_count": 40,
                "major_road_count": 6,
                "total_road_length_m": 6500.0,
                "nearest_road_distance_m": 10.1234,
                "nearest_major_road_distance_m": 55.0,
                "nearest_roads": [
                    {"highway": "motorway", "name": "I-Example", "distance_m": 55.0, "length_m": 1200.0},
                    {"highway": "primary", "name": None, "distance_m": 90.0, "length_m": 800.0},
                    {"highway": "residential", "name": None, "distance_m": 10.1234, "length_m": 120.0},
                ],
            },
            "railways": {
                "radius_m": 1200,
                "rail_count": 1,
                "nearest_rail_distance_m": 120.0,
            },
            "airports": {
                "radius_m": 7000,
                "airport_feature_count": 1,
                "nearest_airport_feature_distance_m": 1500.0,
            },
            "landuse": {"radius_m": 500, "types": ["industrial"]},
        }

        out = estimate_noise(34.000001, -118.000009)

        self.assertIn(out["noise_level"], {"Very High", "High", "Moderate", "Low", "Very Low"})
        self.assertEqual(out["distance_to_road_m"], 10.12)
        self.assertEqual(out["source"], "OpenStreetMap")
        self.assertIn("method", out)
        self.assertIn("factors", out)
        self.assertIn("score_breakdown", out)

        self.assertTrue(mock_set_cache.called)
        cache_key, cache_value = mock_set_cache.call_args.args
        self.assertTrue(cache_key.startswith("noise:"))
        self.assertEqual(cache_value, out)

    @patch("app.services.noise_estimator.get_cached", autospec=True)
    @patch("app.services.noise_estimator._compute_noise_factors", autospec=True)
    def test_estimate_noise_no_road_found(self, mock_compute_noise_factors, mock_get_cached):
        from app.services.noise_estimator import estimate_noise

        mock_get_cached.return_value = None
        mock_compute_noise_factors.return_value = None

        out = estimate_noise(1.0, 2.0)
        self.assertEqual(out, {"error": "No nearby road found"})


if __name__ == "__main__":
    unittest.main()
