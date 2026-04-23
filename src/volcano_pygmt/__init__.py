#!/usr/bin/env python
from importlib.metadata import version

from volcano_pygmt.plot import (
    plot,
    add_inset,
    add_relief,
    create_figure,
    plot_from_dem,
)
from volcano_pygmt.utils import get_region


__version__ = version("volcano-pygmt")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026, Martanto"
__url__ = "https://github.com/martanto/volcano-pygmt"

__all__ = [
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__copyright__",
    "add_inset",
    "add_relief",
    "create_figure",
    "plot_from_dem",
    "plot",
    "get_region",
]
