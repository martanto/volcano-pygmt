#!/usr/bin/env python
from importlib.metadata import version

from volcano_plot.plot import add_inset, add_relief, simple_plot, create_figure
from volcano_plot.config import load_config


load_config()


__version__ = version("volcano-plot")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026, Martanto"
__url__ = "https://github.com/martanto/volcano-plot"

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__copyright__",
    "add_inset",
    "add_relief",
    "create_figure",
    "simple_plot",
    "load_config",
]
