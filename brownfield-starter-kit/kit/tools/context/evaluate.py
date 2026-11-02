"""Final evaluation of the brownfield path: one change, or the whole pilot.

    python tools/context/evaluate.py change CR-042                 # scorecard for one change request
    python tools/context/evaluate.py pilot                         # every recorded episode -> pilot scorecard
    python tools/context/evaluate.py pilot --since 2026-10-01 --out artifacts/evaluation/pilot.md

Deterministic: reads only what the other tools wrote (artifacts/changes/<id>/, artifacts/memory/episodes.jsonl,
artifacts/audit/). It judges the *evidence trail* and the *accuracy of the manifest's predictions*, not code quality
(that is the change-judge / code-review-agent's job).

Scope accuracy, per change (tests excluded on both sides: tests may always change, rule 40.4):
  recall    = predicted ∩ changed / changed     did the manifest anticipate what really had to change?
  precision = predicted ∩ changed / predicted   how much of the predicted scope was actually needed?

Exit codes: 0 PASS, 1 ATTENTION (warnings only), 2 FAIL (a required item is missing or a threshold is breached),
3 nothing to evaluate.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CHANGES, MEMORY, ROOT, brownfield_config, is_test_path, load_yaml, rel  # noqa: E402

DEFAULTS = {                      # override in .claude/config.yaml -> brownfield.evaluation
    "min_scope_recall": 0.90,     # pilot: mean recall below this -> FAIL (manifests miss files that must change)
    "min_scope_precision": 0.50,  # pilot: mean precision below this -> ATTENTION (manifests over-scope)
    "max_fast_track_incidents": 0,  # fast-track changes that failed or touched unpredicted files
    "min_success_rate": 0.80,     # executed changes (not clarify/abandoned) that ended in success
    "min_episodes": 5,            # fewer recorded episodes -> pilot verdict is ATTENTION at best
}
REQUIRED = ["task.md", "context-manifest.yaml", "impact-analysis.md", "change-plan.md", "decision-ledger.md"]
EXECUTED = {"fast-track", "plan-approve-execute", "guarded"}   # workflows that write code (clarify/analyze-only do not)


def settings() -> dict:
    return {**DEFAULTS, **(brownfield_config().get("evaluation") or {})}


def is_test(path: str) -> bool:
    """Test files by brownfield.tests.patterns (any ecosystem: tests/, src/test/, *Test.java, *_test.go, *.spec.ts ...)."""
    name = Path(path).name
    return is_test_path(path) or name.startswith("test_")


def episodes() -> list[dict]:
    if not MEMORY.exists():
        return []
    rows = [json.loads(line) for line in MEMORY.read_text(encoding="utf-8").splitlines() if line.strip()]
    latest = {}
    for row in rows:              # an id can be re-recorded (e.g. clarify, then success): the last line wins
        latest[row["task_id"]] = row
    return list(latest.values())


def effective_workflow(manifest: dict) -> str:
    """The agent's escalation (builder_notes.final_workflow) wins over the tool's selection, as in manifest.py."""
    final = (manifest.get("builder_notes") or {}).get("final_workflow") or {}
    return (final.get("selected") if isinstance(final, dict) else final) or manifest["workflow"]["selected"]


def scope_accuracy(manifest: dict, episode: dict) -> dict:
    predicted = {f for f in set(manifest.get("files", [])) | set(manifest.get("supporting_files") or []) if not is_test(f)}
    changed = {f for f in episode.get("files_changed", []) if not is_test(f)}
    hit = predicted & changed
    return {"predicted": len(predicted), "changed": len(changed), "hit": len(hit),
            "recall": round(len(hit) / len(changed), 2) if changed else None,
            "precision": round(len(hit) / len(predicted), 2) if predicted and changed else None,
            "missed": sorted(changed - predicted)}


def evaluate_change(task_id: str, episode: dict | None = None) -> dict:
    folder = CHANGES / task_id
    findings: list[tuple[str, str]] = []          # (severity FAIL|WARN|INFO, text)
    if not (folder / "context-manifest.yaml").exists():
        return {"task_id": task_id, "verdict": "FAIL", "findings": [("FAIL", f"no manifest at {rel(folder)}/")]}
    manifest = load_yaml(folder / "context-manifest.yaml")
    workflow = effective_workflow(manifest)
    episode = episode or next((e for e in episodes() if e["task_id"] == task_id), None)

    for name in REQUIRED:
        if not (folder / name).exists():
            findings.append(("FAIL", f"missing {name}"))
    audits = sorted(p.name for p in (ROOT / "artifacts" / "audit").glob(f"*{task_id}*.md"))
    if not audits:
        findings.append(("WARN", "no audit file in artifacts/audit/ names this task id"))

    semantic = (manifest.get("seeds") or {}).get("semantic_search")
    if semantic is None:
        findings.append(("WARN", "manifest has no seeds.semantic_search (built before the semantic gate): rebuild it"))
    elif not semantic.get("ran"):
        findings.append(("FAIL", "semantic search did not run for this manifest"))
    critical = (manifest.get("confidence") or {}).get("critical_gaps") or []
    if critical and workflow == "fast-track":
        findings.append(("FAIL", f"fast-track despite critical gaps: {', '.join(map(str, critical))}"))
    blocking = [u["id"] for u in manifest.get("unknowns", []) if u.get("severity") in ("blocking", "major")]
    if blocking:
        findings.append(("INFO", f"major/blocking unknowns recorded: {', '.join(blocking)}"))

    accuracy = None
    if workflow in EXECUTED:
        if not (folder / "verification.md").exists():
            findings.append(("FAIL" if episode and episode["outcome"] == "success" else "WARN",
                             "no verification.md (tests-first evidence, required checks, judge verdict)"))
        if episode is None:
            findings.append(("WARN", "no episode recorded: run tools/context/record_episode.py after the change"))
        else:
            accuracy = scope_accuracy(manifest, episode)
            if accuracy["missed"]:
                sev = "FAIL" if workflow == "fast-track" else "WARN"
                findings.append((sev, f"changed outside the predicted scope: {', '.join(accuracy['missed'])}"
                                      + (" (fast-track incident)" if sev == "FAIL" else "")))
            if episode["outcome"] == "failed":
                findings.append(("FAIL" if workflow == "fast-track" else "WARN", "outcome: failed"))
            if episode.get("repair_iterations", 0) >= 3:
                findings.append(("WARN", "needed the maximum repair iterations"))
    severities = {s for s, _ in findings}
    verdict = "FAIL" if "FAIL" in severities else "ATTENTION" if "WARN" in severities else "PASS"
    return {"task_id": task_id, "objective": manifest["task"]["objective"], "workflow": workflow,
            "confidence": manifest["confidence"]["overall"], "risk": manifest["risk"]["level"],
            "revision": manifest.get("revision", 0), "outcome": episode["outcome"] if episode else None,
            "repair_iterations": episode.get("repair_iterations") if episode else None,
            "accuracy": accuracy, "audits": audits, "verdict": verdict, "findings": findings}


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


def evaluate_pilot(since: str | None) -> dict:
    cfg = settings()
    rows = [e for e in episodes() if not since or e["date"] >= since]
    ids = {e["task_id"] for e in rows}
    if not since:                 # all-time: also changes that never got an episode (clarify, abandoned, in flight)
        ids |= {p.name for p in CHANGES.glob("*") if (p / "context-manifest.yaml").exists()}
    ids = sorted(ids)
    by_id = {e["task_id"]: e for e in rows}
    changes = [evaluate_change(i, by_id.get(i)) for i in ids]
    executed = [c for c in changes if c.get("workflow") in EXECUTED and c.get("outcome") in ("success", "failed")]
    incidents = [c["task_id"] for c in changes if c.get("workflow") == "fast-track" and c.get("outcome") and (
        c["outcome"] == "failed" or (c["accuracy"] and c["accuracy"]["missed"]))]
    calibration = defaultdict(lambda: Counter())
    for c in executed:
        band = "≥0.80" if c["confidence"] >= 0.8 else "0.60–0.79" if c["confidence"] >= 0.6 else "<0.60"
        calibration[band][c["outcome"]] += 1
    metrics = {
        "changes": len(changes), "episodes": len(rows),
        "workflows": dict(Counter(c.get("workflow") for c in changes)),
        "outcomes": dict(Counter(c.get("outcome") or "not recorded" for c in changes)),
        "success_rate": round(sum(c["outcome"] == "success" for c in executed) / len(executed), 2) if executed else None,
        "scope_recall": mean([c["accuracy"]["recall"] for c in executed if c["accuracy"]]),
        "scope_precision": mean([c["accuracy"]["precision"] for c in executed if c["accuracy"]]),
        "fast_track_incidents": incidents,
        "mean_repair_iterations": mean([c["repair_iterations"] for c in executed]),
        "scope_amendments": sum(1 for c in changes if c.get("revision")),
        "calibration": {band: dict(counts) for band, counts in sorted(calibration.items())},
        "change_verdicts": dict(Counter(c["verdict"] for c in changes)),
    }
    gates = []

    def gate(name: str, value, ok: bool | None, severity: str = "FAIL") -> None:
        gates.append({"gate": name, "value": value, "result": "n/a" if ok is None else "pass" if ok else severity})

    gate(f"recorded episodes ≥ {cfg['min_episodes']}", len(rows), len(rows) >= cfg["min_episodes"], "WARN")
    gate(f"fast-track incidents ≤ {cfg['max_fast_track_incidents']}", len(incidents),
         len(incidents) <= cfg["max_fast_track_incidents"])
    gate(f"mean scope recall ≥ {cfg['min_scope_recall']}", metrics["scope_recall"],
         None if metrics["scope_recall"] is None else metrics["scope_recall"] >= cfg["min_scope_recall"])
    gate(f"mean scope precision ≥ {cfg['min_scope_precision']}", metrics["scope_precision"],
         None if metrics["scope_precision"] is None else metrics["scope_precision"] >= cfg["min_scope_precision"], "WARN")
    gate(f"success rate ≥ {cfg['min_success_rate']}", metrics["success_rate"],
         None if metrics["success_rate"] is None else metrics["success_rate"] >= cfg["min_success_rate"])
    gate("no change scorecard FAIL", metrics["change_verdicts"].get("FAIL", 0), not metrics["change_verdicts"].get("FAIL"))
    results = {g["result"] for g in gates}
    verdict = "FAIL" if "FAIL" in results else "ATTENTION" if "WARN" in results or "n/a" in results else "PASS"
    return {"since": since, "metrics": metrics, "gates": gates, "changes": changes, "verdict": verdict}


# --------------------------------------------------------------------------- markdown


def change_md(c: dict) -> str:
    lines = [f"## {c['task_id']} — {c['verdict']}", ""]
    if "objective" in c:
        acc = c["accuracy"]
        lines += ["| Field | Value |", "|---|---|",
                  f"| Objective | {c['objective'].splitlines()[0][:160]} |",
                  f"| Workflow / confidence / risk | {c['workflow']} / {c['confidence']} / {c['risk']} |",
                  f"| Manifest revision (scope changes) | {c['revision']} |",
                  f"| Outcome / repair iterations | {c['outcome'] or 'not recorded'} / {c['repair_iterations']} |",
                  f"| Scope recall / precision | " + (f"{acc['recall']} / {acc['precision']} "
                                                       f"({acc['hit']} of {acc['changed']} changed files predicted, "
                                                       f"{acc['predicted']} predicted)" if acc else "n/a") + " |",
                  f"| Audit files | {', '.join(c['audits']) or 'none'} |", ""]
    lines += [f"- **{s}** {t}" for s, t in c["findings"]] or ["- no findings"]
    return "\n".join(lines) + "\n"


def pilot_md(p: dict) -> str:
    m = p["metrics"]
    lines = [f"# Brownfield pilot evaluation — {p['verdict']}", "",
             f"Generated {date.today().isoformat()} by `tools/context/evaluate.py pilot`"
             + (f" (episodes since {p['since']})" if p["since"] else ""), "", "## Exit gates", "",
             "| Gate | Value | Result |", "|---|---|---|"]
    lines += [f"| {g['gate']} | {g['value']} | {g['result']} |" for g in p["gates"]]
    lines += ["", "## Metrics", "", "| Metric | Value |", "|---|---|",
              f"| Change requests / recorded episodes | {m['changes']} / {m['episodes']} |",
              f"| Workflows | {m['workflows']} |", f"| Outcomes | {m['outcomes']} |",
              f"| Success rate (executed) | {m['success_rate']} |",
              f"| Mean scope recall / precision | {m['scope_recall']} / {m['scope_precision']} |",
              f"| Fast-track incidents | {', '.join(m['fast_track_incidents']) or 'none'} |",
              f"| Mean repair iterations | {m['mean_repair_iterations']} |",
              f"| Changes that needed a scope amendment | {m['scope_amendments']} |",
              f"| Confidence calibration (band → outcomes) | {m['calibration'] or 'n/a'} |",
              f"| Change scorecards | {m['change_verdicts']} |", "", "# Per-change scorecards", ""]
    lines += [change_md(c) for c in p["changes"]]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("change", help="scorecard for one change request")
    one.add_argument("task_id")
    allp = sub.add_parser("pilot", help="aggregate scorecard over every change / episode")
    allp.add_argument("--since", help="only episodes on or after this date (YYYY-MM-DD)")
    for p in (one, allp):
        p.add_argument("--out", type=Path, help="write the markdown report here (default: stdout)")
        p.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    args = parser.parse_args()

    if args.cmd == "change":
        result = evaluate_change(args.task_id)
        text = json.dumps(result, indent=2, default=str) if args.json else change_md(result)
    else:
        result = evaluate_pilot(args.since)
        if not result["changes"]:
            print("nothing to evaluate: no manifests under artifacts/changes/ and no episodes")
            return 3
        text = json.dumps(result, indent=2, default=str) if args.json else pilot_md(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"{result['verdict']} -> {rel(args.out)}")
    else:
        print(text)
    return {"PASS": 0, "ATTENTION": 1, "FAIL": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
