"""Unit tests for volcano_plot.utils."""
import math
import tempfile
from pathlib import Path

import pytest

from volcano_plot.utils import ensure_dir, km_to_degrees, slugify


class TestKmToDegrees:
    def test_equator_lat(self):
        lat_deg, lon_deg = km_to_degrees(111.32, 0.0)
        assert math.isclose(lat_deg, 1.0, rel_tol=1e-6)
        assert math.isclose(lon_deg, 1.0, rel_tol=1e-6)

    def test_lat_deg_independent_of_latitude(self):
        lat_deg_0, _ = km_to_degrees(10.0, 0.0)
        lat_deg_45, _ = km_to_degrees(10.0, 45.0)
        assert math.isclose(lat_deg_0, lat_deg_45, rel_tol=1e-9)

    def test_lon_deg_scales_with_latitude(self):
        _, lon_deg_0 = km_to_degrees(10.0, 0.0)
        _, lon_deg_60 = km_to_degrees(10.0, 60.0)
        # At 60° lat, cos(60°)=0.5, so lon_deg should be ~double that at equator
        assert math.isclose(lon_deg_60, lon_deg_0 * 2, rel_tol=1e-6)

    def test_returns_tuple_of_two_floats(self):
        result = km_to_degrees(5.0, 10.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_raises_at_north_pole(self):
        with pytest.raises(ValueError, match="90"):
            km_to_degrees(10.0, 90.0)

    def test_raises_at_south_pole(self):
        with pytest.raises(ValueError, match="-90"):
            km_to_degrees(10.0, -90.0)

    def test_zero_km(self):
        lat_deg, lon_deg = km_to_degrees(0.0, 30.0)
        assert lat_deg == 0.0
        assert lon_deg == 0.0

    def test_negative_km(self):
        lat_deg, lon_deg = km_to_degrees(-10.0, 0.0)
        assert lat_deg < 0
        assert lon_deg < 0

    def test_negative_latitude(self):
        _, lon_deg_pos = km_to_degrees(10.0, 45.0)
        _, lon_deg_neg = km_to_degrees(10.0, -45.0)
        assert math.isclose(lon_deg_pos, lon_deg_neg, rel_tol=1e-9)


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_custom_separator(self):
        assert slugify("Hello World", hyphen="_") == "hello_world"

    def test_multiple_spaces_collapsed(self):
        assert slugify("  Multiple   Spaces  ") == "multiple-spaces"

    def test_underscores_replaced(self):
        assert slugify("hello_world") == "hello-world"

    def test_special_characters_stripped(self):
        assert slugify("hello@world!") == "helloworld"

    def test_already_lowercase(self):
        assert slugify("already") == "already"

    def test_numbers_preserved(self):
        assert slugify("volcano 2024") == "volcano-2024"

    def test_leading_trailing_separator_stripped(self):
        assert not slugify("-hello-").startswith("-")
        assert not slugify("-hello-").endswith("-")

    def test_empty_string(self):
        assert slugify("") == ""

    def test_consecutive_separators_collapsed(self):
        assert slugify("a--b") == "a-b"

    def test_mixed_case(self):
        assert slugify("UPPER lower MiXeD") == "upper-lower-mixed"


class TestEnsureDir:
    def test_creates_new_directory(self, tmp_path):
        target = tmp_path / "new_dir"
        result = ensure_dir(target)
        assert result.is_dir()

    def test_creates_nested_directories(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        result = ensure_dir(target)
        assert result.is_dir()

    def test_returns_path_object(self, tmp_path):
        result = ensure_dir(tmp_path / "x")
        assert isinstance(result, Path)

    def test_existing_directory_no_error(self, tmp_path):
        ensure_dir(tmp_path)
        result = ensure_dir(tmp_path)
        assert result.is_dir()

    def test_accepts_string_path(self, tmp_path):
        target = str(tmp_path / "from_string")
        result = ensure_dir(target)
        assert result.is_dir()

    def test_file_in_path_raises(self, tmp_path):
        file = tmp_path / "file.txt"
        file.write_text("data")
        with pytest.raises((NotADirectoryError, OSError)):
            ensure_dir(file / "subdir")
