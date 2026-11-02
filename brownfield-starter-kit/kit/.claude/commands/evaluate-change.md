---
description: Brownfield final evaluation of ONE change request — scores the evidence trail (manifest, impact analysis, plan, ledger, verification, audit) and the manifest's prediction accuracy (scope recall/precision, fast-track incidents) with tools/context/evaluate.py. Run after /implement-change (or after a clarify / abandoned CR is closed).
argument-hint: "<task-id>"
---

# /evaluate-change

Task id: $ARGUMENTS

## Objective
Produce `artifacts/changes/<task-id>/evaluation.md`: a deterministic scorecard from `tools/context/evaluate.py change`
plus a short judgement. Evaluates **how well the brownfield path worked for this change**, not the code itself (that
was change-judge / code-review-agent in `/implement-change`). Writes no product code.

## When to use
| Situation | Command |
|---|---|
| `/implement-change` finished (PASS or needs_human) | **`/evaluate-change <id>`** |
| A CR ended in `clarify` or was abandoned | `record_episode.py <id> --outcome clarify` (or `abandoned`), then **`/evaluate-change <id>`** |
| End of a pilot / sprint, many CRs | `/evaluate-pilot` |

## Runtime Inputs
### Required
- `artifacts/changes/<task-id>/context-manifest.yaml`

### Expected (missing ones are findings, not blockers)
- `task.md`, `impact-analysis.md`, `change-plan.md`, `decision-ledger.md`, `verification.md` (executed workflows)
- an episode line in `artifacts/memory/episodes.jsonl` (`tools/context/record_episode.py`)
- `artifacts/audit/*<task-id>*.md`

## Use Agents
`orchestrator-agent → quality-agent`

## Delegate to Subagents
audit-trail-writer

## Execution order
```
python tools/context/evaluate.py change <id> --out artifacts/changes/<id>/evaluation.md
  exit 0 PASS | 1 ATTENTION | 2 FAIL
 -> read the scorecard; for every FAIL / WARN finding append one line: cause + owner + fix
    (e.g. "missed file X: seed missing from manifest -> next time --seed svc:sym; lesson recorded")
 -> if the scorecard shows a miss and the episode has no lesson: ask the human for one, then re-record the
    episode (record_episode.py appends; evaluate.py uses the last line per id)
 -> audit
```

## Enforce Rules
00, 09, 10, 22, 40

## Command-Specific Hardening
- The scorecard section is tool output: never hand-edit numbers or verdicts. The judgement is appended below it.
- A FAIL is not waived here. A fast-track incident (a fast-track change that failed or changed files outside the
  manifest) is reported to the human and recorded as a lesson; it counts against the pilot exit gate.
- Do not "fix" findings by back-filling artifacts after the fact (e.g. writing a verification.md for checks that were
  not run). Missing evidence stays missing.

## Definition of Done
- [ ] `evaluation.md` written by the tool, judgement appended, exit code reported
- [ ] Every FAIL / WARN has cause + owner + fix
- [ ] `artifacts/audit/<date>-evaluate-change-<id>.md`

## Next command
> ✅ `/evaluate-change <id>`: **<PASS | ATTENTION | FAIL>** (recall <r>, precision <p>).
> **Next:** the next `/build-context`, or `/evaluate-pilot` at the end of the pilot.
