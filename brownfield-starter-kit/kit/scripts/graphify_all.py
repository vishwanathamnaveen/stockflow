"""Build graphify knowledge graphs: one per service, one for the shared library (brownfield.layout.common_root,
when the repo has one) and one for the whole application (repo root).

    python scripts/graphify_all.py                   # every service + common + overall
    python scripts/graphify_all.py orders overall    # a subset
    python scripts/graphify_all.py --label           # name communities with an LLM (claude CLI)

Each target gets <target>/graphify-out/:
  graph.json             the knowledge graph (nodes, edges, communities), enriched by
                         tools/context/enrich_graph.py with signature, docstring, route, events, BRs, tests
  GRAPH_REPORT.md        god nodes, surprising connections, communities, import cycles
  graph.html             interactive force-directed graph
  GRAPH_TREE.html        collapsible file -> symbol tree
  <name>-callflow.html   Mermaid architecture / call-flow diagrams

Extraction is local AST parsing with graphify's tree-sitter grammars (about 40 languages, no API key). When a service
lives at the repository root, its graph *is* the overall graph, so `overall` is skipped. --label sends community
summaries to the configured LLM backend to replace "Community N" names.
Query a graph with e.g. `graphify query "how is an order approved?" --graph <target>/graphify-out/graph.json`.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from _paths import COMMON, ROOT, has_common, registry, service_dir

PROJECT = (yaml.safe_load((ROOT / ".claude" / "config.yaml").read_text(encoding="utf-8")) or {}).get("project", {}).get(
    "name", ROOT.name) if (ROOT / ".claude" / "config.yaml").exists() else ROOT.name


def targets() -> dict[str, Path]:
    found = {"common": COMMON} if has_common() else {}
    for name in registry():
        found[name] = service_dir(name)
    if not any(Path(d).resolve() == ROOT.resolve() for d in found.values()):
        found["overall"] = ROOT
    return found


def _graphify() -> str:
    exe = shutil.which("graphify", path=str(Path(sys.executable).parent)) or shutil.which("graphify")
    if exe is None:
        raise SystemExit("graphify is not installed; run: pip install -r requirements.txt")
    return exe


def build(graphify: str, name: str, directory: Path, label: bool, backend: str) -> bool:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    naming = [f"--backend={backend}"] if label else ["--no-label"]
    steps = [
        [graphify, "extract", ".", "--code-only", "--force"],
        [graphify, "cluster-only", ".", *naming],
        # graphify stores no signatures/docstrings/end lines: add them (+ routes, events, BRs, tests) to graph.json
        [sys.executable, str(ROOT / "tools" / "context" / "enrich_graph.py"), name],
        [graphify, "tree", "--graph", "graphify-out/graph.json", "--output", "graphify-out/GRAPH_TREE.html",
         "--label", f"{PROJECT}-{name}"],
        [graphify, "export", "callflow-html", "."],
    ]
    for cmd in steps:
        result = subprocess.run(cmd, cwd=directory, env=env, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            print(f"  FAIL  {name:<13} {' '.join(cmd[1:3])}\n{result.stdout}{result.stderr}")
            return False
    report = (directory / "graphify-out" / "GRAPH_REPORT.md").read_text(encoding="utf-8")
    summary = next((line[2:] for line in report.splitlines() if line.startswith("- ") and "nodes" in line), "")
    print(f"  OK    {name:<13} {summary.replace(' · ', ', ')}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="subset of targets (service names, 'common', 'overall')")
    parser.add_argument("--label", action="store_true", help="name communities with an LLM backend")
    parser.add_argument("--backend", default="claude-cli", help="LLM backend for --label (default: claude-cli)")
    args = parser.parse_args()

    selected = targets()
    if args.names:
        unknown = set(args.names) - set(selected) - {"overall"}   # overall: absent when a service is the root
        if unknown:
            raise SystemExit(f"unknown targets: {', '.join(sorted(unknown))}; choose from {', '.join(selected)}")
        selected = {k: v for k, v in selected.items() if k in args.names}

    graphify = _graphify()
    failed = [name for name, directory in selected.items() if not build(graphify, name, directory, args.label, args.backend)]
    print("\nFAILED: " + ", ".join(failed) if failed else "\nall graphs built")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
