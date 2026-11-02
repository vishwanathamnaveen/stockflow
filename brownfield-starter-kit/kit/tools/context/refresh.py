"""Refresh system intelligence before building a manifest or after a change lands.

    python tools/context/refresh.py orders               # service graph + code graph (graphify + enrichment) + semantic index
    python tools/context/refresh.py orders --tests       # also re-run tests -> per-test coverage (quality graph)
    python tools/context/refresh.py --check orders       # report freshness only, change nothing (no names = every service)
    python tools/context/refresh.py --stale              # refresh only what changed (hooks / agents / CI)
    python tools/context/refresh.py --check --committed-only   # portable check of committed artifacts (CI)

What is stale, and what --stale rebuilds:
  code graph      a service source file changed / new / deleted, or tooling/config  -> graphify + enrichment
                  only business rules, coverage or published topics changed          -> enrichment only (seconds)
  service graph   config, contracts or service-package code changed (traces never)   -> service_graph.py
  semantic index  the corpus it would build now differs from the indexed one         -> re-embed changed docs only
  knowledge base  a document under knowledge/ is added, changed or removed          -> re-extract + re-embed that file

Guarantees: one refresh at a time (var/context/refresh.lock); stages stop at the first failure; the inputs are
digested before and after, and a refresh whose inputs moved underneath it is retried once, then fails; every
refreshed artifact is re-checked before success is reported. The result is recorded in var/context/snapshot.json
with the source-state digest, base commit and whether the working tree differed from it (pre-commit refreshes
have no SHA of their own).

Exit code 0 = fresh (or refreshed), 1 = a step failed, 2 = --check found stale artifacts, 3 = another refresh holds
the lock.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import service_graph  # noqa: E402
from common import (CONTEXT_ENGINE_VERSION, LOCAL_STATE, QUALITY, ROOT, RefreshLocked, build_config_hash,  # noqa: E402
                    code_targets, load_json, refresh_lock, registry, rel, source_state, source_state_files, symbol_index,
                    write_atomic)
from manifest import graph_freshness  # noqa: E402

SNAPSHOT = LOCAL_STATE / "snapshot.json"
ATTEMPTS = 2


def targets() -> list[str]:
    """Every per-target code graph: the services plus the shared library (the overall graph is rebuilt with them)."""
    return sorted(code_targets())


def _run(cmd: list[str]) -> bool:
    print("$", " ".join(cmd[1:]) if cmd[0] == sys.executable else " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=ROOT) == 0


def _index_freshness() -> dict:
    try:
        import semantic_index
    except ImportError as exc:
        return {"state": "unavailable", "reason": f"{exc.name} not installed"}
    return semantic_index.freshness()


def _kb_freshness() -> dict:
    """`absent` when there are no documents under the knowledge roots and no index: the stage is skipped."""
    try:
        import knowledge_base
        return knowledge_base.freshness()
    except ImportError as exc:
        return {"state": "unavailable", "reason": f"{exc.name} not installed"}


def status(services: list[str], *, committed_only: bool = False, skip_index: bool = False) -> dict[str, dict]:
    report = {}
    for service in services:
        fresh = graph_freshness(service, include_local=not committed_only)
        report[service] = {"code_graph": fresh["code_graph"], "rebuild": fresh["rebuild"],
                           "stale_files": fresh["stale_files"]}
        if not committed_only:
            report[service]["coverage"] = "present" if (QUALITY / f"{service}-coverage.json").exists() else "missing"
    report["service-graph"] = service_graph.freshness()
    if not (skip_index or committed_only):
        report["semantic-index"] = _index_freshness()
        kb = _kb_freshness()
        if kb["state"] != "absent":
            report["knowledge-base"] = kb
    return report


def is_stale(report: dict[str, dict], *, coverage: bool = True) -> bool:
    for name, info in report.items():
        if name in ("service-graph", "semantic-index", "knowledge-base"):
            if info["state"] != "fresh":
                return True
        elif info["code_graph"] != "fresh" or (coverage and info.get("coverage") == "missing"):
            return True
    return False


def refresh_once(explicit: list[str], stale: bool) -> tuple[bool, dict]:
    """One pass, in dependency order; stops at the first failed stage (later stages read earlier outputs)."""
    symbol_index.cache_clear()   # a retry must see the code as it is now, not as the previous attempt parsed it
    done = {"graphify": [], "enrich": []}
    # first: enrichment reads its publish edges, and its freshness compares against them
    if not _run([sys.executable, "tools/context/service_graph.py"]):
        return False, done
    graphify, enrich = set(explicit), set()
    if stale:
        for s in targets():
            f = graph_freshness(s)
            if f["code_graph"] != "fresh":
                (graphify if f["rebuild"] == "graphify" else enrich).add(s)
    enrich -= graphify
    if graphify:
        done["graphify"] = sorted(graphify)
        if not _run([sys.executable, "scripts/graphify_all.py", *done["graphify"], "overall"]):
            return False, done
    if enrich:   # the overall graph was already re-enriched by graphify_all when it ran
        done["enrich"] = sorted(enrich)
        if not _run([sys.executable, "tools/context/enrich_graph.py", *done["enrich"], *([] if graphify else ["overall"])]):
            return False, done
    if not _run([sys.executable, "tools/context/semantic_index.py", "build"]):
        return False, done
    if _kb_freshness()["state"] != "absent" and not _run([sys.executable, "tools/context/knowledge_base.py", "build"]):
        return False, done
    return True, done


def _counts(path: Path) -> dict:
    if not path.exists():
        return {}
    meta = load_json(path)
    return {k: meta.get(k) for k in ("documents", "embedded_now", "reused", "removed", "model")}


def _semantic_counts() -> dict:
    return _counts(ROOT / "graphs" / "semantic" / "meta.json")


def _kb_counts() -> dict:
    return _counts(ROOT / "graphs" / "kb" / "meta.json")


def _print(report: dict[str, dict]) -> None:
    for name, info in report.items():
        print(f"{name:<14} {info}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("services", nargs="*", choices=targets() + [[]], default=[])
    parser.add_argument("--stale", action="store_true", help="select everything whose inputs changed")
    parser.add_argument("--tests", action="store_true", help="re-run test suites to refresh per-test coverage")
    parser.add_argument("--check", action="store_true", help="only report freshness (default: every service)")
    parser.add_argument("--committed-only", action="store_true",
                        help="with --check: only artifacts reproducible from git (skip coverage and the semantic index)")
    parser.add_argument("--skip-index", action="store_true", help="with --check: do not check the semantic index")
    args = parser.parse_args(argv)

    if args.check:
        report = status(args.services or targets(), committed_only=args.committed_only,
                        skip_index=args.skip_index)
        _print(report)
        return 2 if is_stale(report) else 0
    if not (args.services or args.stale):
        parser.error("name at least one service, or use --stale")
    if args.stale and not args.services and not args.tests \
            and not is_stale(status(targets()), coverage=False):
        print("all code graphs, the service graph, the semantic index and the knowledge base are fresh")
        return 0

    try:
        with refresh_lock():
            tested = []
            if args.tests:   # before the guarded loop: tests rewrite coverage, which is itself an input
                tested = sorted(set(args.services) | ({s for s in targets() if graph_freshness(s)["code_graph"] != "fresh"}
                                                      if args.stale else set()))
                if tested and not _run([sys.executable, "scripts/run_tests.py", *tested]):
                    print("FAILED: tests failed; graphs and index were not refreshed")
                    return 1
            for attempt in range(1, ATTEMPTS + 1):
                before = source_state_files()
                ok, done = refresh_once(args.services, args.stale)
                done["tests"] = tested
                if not ok:
                    print("FAILED: a refresh stage failed; artifacts after it were not rebuilt (see output above)")
                    return 1
                after = source_state_files()
                if after == before:
                    break
                moved = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
                print(f"inputs changed during refresh (attempt {attempt}/{ATTEMPTS}): {', '.join(moved[:5])}")
            else:
                print("FAILED: inputs kept changing during the refresh; stop editing and run it again")
                return 1
            touched = sorted(set(args.services) | set(done["graphify"]) | set(done["enrich"])
                             | (set(targets()) if args.stale else set()))
            report = status(touched)
            _print(report)
            stale = [n for n, i in report.items() if (i.get("state") or i.get("code_graph")) != "fresh"]
            if stale:
                print(f"FAILED: still stale after refresh: {', '.join(stale)}")
                return 1
            state = source_state(after)
            snapshot = {**state, "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "engine_version": CONTEXT_ENGINE_VERSION, "config_hash": build_config_hash(),
                        "refreshed": done, "semantic_index": _semantic_counts(),
                        "knowledge_base": _kb_counts(), "status": report}
            write_atomic(SNAPSHOT, json.dumps(snapshot, indent=2))
    except RefreshLocked as exc:
        print(f"BLOCKED: {exc}")
        return 3
    sem = snapshot["semantic_index"]
    print(f"\nsnapshot {state['source_state_digest']}  base {state['base_commit']}  working_tree={state['working_tree']}"
          f"\n  graphify: {done['graphify'] or '-'}  enrich-only: {done['enrich'] or '-'}  tests: {done['tests'] or '-'}"
          f"\n  semantic index: {sem.get('documents')} docs ({sem.get('embedded_now')} embedded, "
          f"{sem.get('reused')} reused, {sem.get('removed')} removed)")
    kb = snapshot["knowledge_base"]
    if kb:
        print(f"  knowledge base: {kb.get('documents')} passages ({kb.get('embedded_now')} embedded, "
              f"{kb.get('reused')} reused, {kb.get('removed')} removed)")
    print(f"  -> {rel(SNAPSHOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
