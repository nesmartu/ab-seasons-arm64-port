#!/usr/bin/env python3
"""Install the shared pinned toolchain for both Seasons bridges."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[2]/'tools/setup_toolchain.py'), run_name='__main__')
