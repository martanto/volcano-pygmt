#!/usr/bin/env python
from importlib.metadata import version

from volcano_plot.config import load_config


load_config()
import pygmt


__version__ = version("volcano-plot")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026, Martanto"
__url__ = "https://github.com/martanto/volcano-plot"

__all__ = ["pygmt", "load_config"]
