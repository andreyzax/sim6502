#!/usr/bin/env python3
"""Wrapper script to profile the main.py script."""

import cProfile
import pathlib
import pstats
import runpy
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

pr = cProfile.Profile()
pr.enable()

try:
    runpy.run_path(str(PROJECT_ROOT / "main.py"), run_name="__main__")
except KeyboardInterrupt:
    pass
finally:
    pr.disable()
    last = max((int(f.suffix[1:]) for f in (PROJECT_ROOT / ".prof").glob("pstats.*")))
    next = last + 1
    new_pstats = str(PROJECT_ROOT / ".prof" / f"pstats.{next}")
    pr.dump_stats(new_pstats)

    stats = pstats.Stats(new_pstats)
    stats.strip_dirs()
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(0.02)
