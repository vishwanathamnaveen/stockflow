"""Path helpers shared by the scripts. The layout (services root, optional shared library) comes from
brownfield.layout in .claude/config.yaml via tools/context/common.py, so scripts and tools never disagree."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "context"))
from common import (COMMON, SERVICES, code_targets, common_package, has_common, package_dir, registry,  # noqa: E402,F401
                    service_dir)

if has_common() and str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))

