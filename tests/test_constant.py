"""Unit tests for volcano_pygmt.constant."""
from volcano_pygmt.constant import COUNTRY_REGIONS


class TestCountryRegions:
    def test_is_dict(self):
        assert isinstance(COUNTRY_REGIONS, dict)

    def test_indonesia_present(self):
        assert "Indonesia" in COUNTRY_REGIONS

    def test_each_region_has_four_values(self):
        for country, bounds in COUNTRY_REGIONS.items():
            assert len(bounds) == 4, f"{country} should have 4 bounding values"

    def test_bounds_are_numeric(self):
        for country, bounds in COUNTRY_REGIONS.items():
            for v in bounds:
                assert isinstance(v, (int, float)), f"{country} bound {v!r} is not numeric"

    def test_indonesia_bounds_order(self):
        lon_min, lon_max, lat_min, lat_max = COUNTRY_REGIONS["Indonesia"]
        assert lon_min < lon_max, "lon_min must be less than lon_max"
        assert lat_min < lat_max, "lat_min must be less than lat_max"

    def test_indonesia_longitude_range(self):
        lon_min, lon_max, _, _ = COUNTRY_REGIONS["Indonesia"]
        assert -180 <= lon_min <= 180
        assert -180 <= lon_max <= 180

    def test_indonesia_latitude_range(self):
        _, _, lat_min, lat_max = COUNTRY_REGIONS["Indonesia"]
        assert -90 <= lat_min <= 90
        assert -90 <= lat_max <= 90
