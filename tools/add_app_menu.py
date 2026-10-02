#!/usr/bin/env python3
"""Retired: the app menu is now part of the shared site header.

Kept so old notes and muscle memory still work. It just runs tools/build_chrome.py, which writes
the header, footer and apps hub from tools/apps.json. See tools/README.md.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("build_chrome.py")), run_name="__main__")
