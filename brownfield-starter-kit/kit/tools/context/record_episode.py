"""Append a completed (or abandoned) change to episodic memory.

    python tools/context/record_episode.py CR-042 --outcome success --lessons "billing caches order totals; invalidate on order.updated"

Reads artifacts/changes/<id>/context-manifest.yaml, adds the files actually changed
(git diff against the manifest's commit) and appends one JSON line to
artifacts/memory/episodes.jsonl. tools/context/manifest.py surfaces earlier
episodes that touched the same files in the `memory` section of new manifests.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CHANGES, COMMON, MEMORY, git, has_git, in_service, is_test_path, load_json, load_yaml,  # noqa: E402
                    product_files, registry, rel, service_dir, business_rule_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task_id")
    parser.add_argument("--outcome", required=True, choices=["success", "failed", "abandoned", "clarify"])
    parser.add_argument("--lessons", default="", help="what the next change in this area should know")
    parser.add_argument("--repair-iterations", type=int, default=0)
    parser.add_argument("--files", nargs="+", help="files the change touched (default: product paths changed since "
                                                   "the manifest commit); pass explicitly when the tree has unrelated work")
    args = parser.parse_args()

    path = CHANGES / args.task_id / "context-manifest.yaml"
    if not path.exists():
        raise SystemExit(f"no manifest at {rel(path)}; run tools/context/manifest.py first")
    manifest = load_yaml(path)
    baseline = CHANGES / args.task_id / "baseline.json"
    if args.files:
        changed = sorted(args.files)
    elif not has_git() or (not manifest["task"].get("commit") and baseline.exists()):
        # no version control: the change is what differs from the content snapshot taken with the manifest
        if not baseline.exists():
            raise SystemExit(f"no git and no {rel(baseline)}: pass the touched files with --files")
        before, now = load_json(baseline)["files"], product_files()
        changed = sorted(f for f in set(before) | set(now) if before.get(f) != now.get(f))
    else:
        # Only product paths count as "the change". A dirty working tree with unrelated work (tooling, docs, other
        # tasks) must not leak into this episode's file list, which future manifests match on (BUG-2).
        base = manifest["task"].get("commit") or "HEAD"
        code_dirs = [service_dir(s) for s in registry()] + ([COMMON] if COMMON is not None else [])
        product = tuple(("." if rel(p) in ("", ".") else rel(p) + "/") for p in code_dirs) + ("contracts/", "config/")
        product += tuple(rel(p) for p in business_rule_files())
        # a service at the repo root covers everything: keep the kit's own outputs out
        outputs = (":(exclude)artifacts", ":(exclude)graphs", ":(exclude)var", ":(exclude).claude", ":(exclude)tools/context")
        candidates = set(git("diff", "--name-only", base, "--", *product, *outputs).splitlines())
        candidates |= {l[3:] for l in git("status", "--porcelain", "-uall", "--", *product, *outputs).splitlines()
                       if l.startswith("??")}
        noise = ("graphify-out", "__pycache__", ".pytest_cache", "/target/", "/build/", "node_modules/", "/bin/", "/obj/")
        changed = sorted(f for f in candidates if not any(n in f for n in noise) and not f.endswith(("/", ".pyc")))
    # Expected scope = manifest files + supporting files + the tests of the services whose files are in scope.
    predicted = set(manifest.get("files", [])) | set(manifest.get("supporting_files", []))
    scoped = {s for s in registry() if any(in_service(f, s) for f in manifest.get("files", []))}
    expected = lambda f: f in predicted or (is_test_path(f) and any(in_service(f, s) for s in scoped))  # noqa: E731
    episode = {
        "task_id": args.task_id,
        "date": date.today().isoformat(),
        "objective": manifest["task"]["objective"],
        "type": manifest["task"]["type"],
        "service": manifest["services"]["primary"],
        "impacted": manifest["services"]["impacted"],
        "workflow": manifest["workflow"]["selected"],
        "confidence": manifest["confidence"]["overall"],
        "risk": manifest["risk"]["level"],
        "files": sorted(set(manifest.get("files", [])) | set(changed)),
        "files_changed": changed,
        "unpredicted_files": sorted(f for f in changed if not expected(f)),
        "manifest_revision": manifest.get("revision", 0),
        "outcome": args.outcome,
        "repair_iterations": args.repair_iterations,
        "lessons": args.lessons,
    }
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(episode) + "\n")
    print(f"recorded {args.task_id} ({args.outcome}); unpredicted files: {episode['unpredicted_files'] or 'none'} -> {rel(MEMORY)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
