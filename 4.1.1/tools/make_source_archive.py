#!/usr/bin/env python3
"""Archive the complete repository, including shared 4.1.1 dependencies."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parents[2]/'tools/make_source_archive.py'), run_name='__main__')
