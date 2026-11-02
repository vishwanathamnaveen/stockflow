---
description: Brownfield final evaluation of the WHOLE pilot — aggregates every change request and episode with tools/context/evaluate.py pilot (success rate, scope recall/precision, fast-track incidents, confidence calibration, scope amendments) against the exit gates in brownfield.evaluation, and recommends go / extend / stop for widening enabled_services.
argument-hint: "[since=YYYY-MM-DD]"
---

# /evaluate-pilot

Arguments: $ARGUMENTS

## Objective
Decide, with evidence, whether the brownfield path is ready to be enabled for more services. Output:
`artifacts/evaluation/<YYYY-MM-DD>-pilot-evaluation.md` (tool scorecard + recommendation). Writes no product code and
never edits `brownfield.enabled_services` itself.

## Runtime Inputs
### Optional
- `since=`: only episodes on or after this date (the pilot window)

## Use Agents
`orchestrator-agent → quality-agent`

## Delegate to Subagents
audit-trail-writer, harness-updater

## Execution order
```
python tools/context/refresh.py --check          # system intelligence still fresh? (report it, do not fix here)
python tools/context/evaluate.py pilot [--since <date>] --out artifacts/evaluation/<date>-pilot-evaluation.md
  exit 0 PASS | 1 ATTENTION | 2 FAIL | 3 nothing to evaluate
 -> append "## Recommendation":
      PASS       -> GO: propose the next services for enabled_services (a human edits the config)
      ATTENTION  -> EXTEND: which gate is n/a or WARN, how many more CRs are needed
      FAIL       -> STOP: incidents / misses, their lessons, and what must change (seeds, docs, tests, thresholds)
 -> append "## Calibration": does a higher confidence band really succeed more often? If not, propose new
    brownfield.confidence thresholds (a human decides)
 -> append "## Top lessons": from the episodes' lessons, grouped by service
 -> audit + harness
```

## Exit gates (defaults; `brownfield.evaluation` in `.claude/config.yaml`)
| Gate | Default | Failing it means |
|---|---|---|
| recorded episodes | ≥ 5 | too little evidence (ATTENTION) |
| fast-track incidents | ≤ 0 | the cheapest workflow let something through: **STOP** |
| mean scope recall | ≥ 0.90 | manifests miss files that must change |
| mean scope precision | ≥ 0.50 | manifests over-scope (ATTENTION) |
| success rate (executed CRs) | ≥ 0.80 | changes fail even after context was built |
| change scorecards with FAIL | 0 | an individual change broke the evidence trail |

## Enforce Rules
00, 09, 10, 22, 40

## Command-Specific Hardening
- Thresholds are changed only by a human in `.claude/config.yaml`, never to make a pilot pass.
- The recommendation cites gate values from the scorecard; no unsupported claims.

## Definition of Done
- [ ] Freshness reported; scorecard written by the tool; recommendation, calibration and lessons appended
- [ ] `artifacts/audit/<date>-evaluate-pilot.md`; harness updated (phase-changing)

## Next command
> ✅ `/evaluate-pilot`: **<GO | EXTEND | STOP>**.
> **Next:** a human updates `brownfield.enabled_services` (GO), runs more CRs (EXTEND), or fixes the listed causes (STOP).
