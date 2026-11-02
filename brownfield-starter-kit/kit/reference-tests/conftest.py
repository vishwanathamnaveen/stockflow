"""Portable reference tests of the context engine: inline fixtures only, so they pass in any repository.

  test_languages.py       language adapters, convention presets, coverage formats, QA test cases
  test_knowledge_base.py  document knowledge base (PDF, Excel, CSV, notes), exclusion of unsafe passages
  test_discovery.py       layout discovery used by install.py

Installed as tools/context/reference-tests/; run with `python -m pytest tools/context/reference-tests -q`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
