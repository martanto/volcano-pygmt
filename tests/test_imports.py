"""Circular / smoke import tests — verifies the package can be imported without errors."""
import importlib
import sys


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_utils_importable():
    mod = _fresh_import("volcano_pygmt.utils")
    assert hasattr(mod, "km_to_degrees")
    assert hasattr(mod, "slugify")
    assert hasattr(mod, "ensure_dir")


def test_constant_importable():
    mod = _fresh_import("volcano_pygmt.constant")
    assert hasattr(mod, "COUNTRY_REGIONS")
    assert isinstance(mod.COUNTRY_REGIONS, dict)


def test_logger_importable():
    mod = _fresh_import("volcano_pygmt.logger")
    assert hasattr(mod, "logger")


def test_package_importable():
    import volcano_pygmt
    assert hasattr(volcano_pygmt, "__version__")
    assert hasattr(volcano_pygmt, "simple_plot")
    assert hasattr(volcano_pygmt, "create_figure")


def test_no_circular_import():
    """Re-importing submodules after the package is loaded must not raise."""
    import volcano_pygmt  # noqa: F401
    importlib.import_module("volcano_pygmt.utils")
    importlib.import_module("volcano_pygmt.constant")
    importlib.import_module("volcano_pygmt.logger")
