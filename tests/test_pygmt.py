"""Tests that GMT_LIBRARY_PATH is configured and PyGMT loads successfully."""
import os
from pathlib import Path

import pytest


def test_gmt_library_path_set():
    assert os.environ.get("GMT_LIBRARY_PATH", "").strip(), (
        "GMT_LIBRARY_PATH is not set. Add it to your .env file."
    )


def test_gmt_library_path_exists_on_disk():
    gmt_path = os.environ.get("GMT_LIBRARY_PATH", "").strip()
    assert Path(gmt_path).is_dir(), (
        f"GMT_LIBRARY_PATH={gmt_path!r} does not point to an existing directory."
    )


def test_gmt_library_path_in_system_path():
    gmt_path = os.environ.get("GMT_LIBRARY_PATH", "").strip()
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    assert gmt_path in path_dirs, (
        f"GMT_LIBRARY_PATH={gmt_path!r} was not prepended to PATH."
    )


def test_pygmt_importable():
    try:
        import pygmt  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Failed to import pygmt: {exc}")


def test_pygmt_version_accessible():
    import pygmt
    assert hasattr(pygmt, "__version__"), "pygmt has no __version__ attribute"
    assert pygmt.__version__, "pygmt.__version__ is empty"


def test_pygmt_show_versions():
    """pygmt.show_versions() must run without error (validates GMT shared lib linkage)."""
    import pygmt
    try:
        pygmt.show_versions()
    except Exception as exc:
        pytest.fail(f"pygmt.show_versions() raised: {exc}")
