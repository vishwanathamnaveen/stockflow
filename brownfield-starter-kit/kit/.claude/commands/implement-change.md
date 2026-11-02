---
description: Brownfield code change — implement a task from its finalized Context Manifest and change plan (from /build-context), with risk-based gates, regression across impacted services, judge + repair loop, ledger and memory.
argument-hint: "<task-id>"
---

# /implement-change

Task id: $ARGUMENTS

## Objective
Implement `artifacts/changes/<task-id>/change-plan.md` inside the manifest's blast radius, prove it with the manifest's
regression set, and update system intelligence. Does **not** build context (that is `/build-context`).

## When to use
After `/build-context` produced `Status: Ready`, and — for `plan-approve-execute` / `guarded` — after a human wrote
`Approval: Approved by <name> <YYYY-MM-DD>` in the plan.

## Runtime Inputs

### Required
- `task-id` with `artifacts/changes/<task-id>/{context-manifest.yaml, change-plan.md}`

### Optional
- `repair_budget` (≤ 3)

## Use Agents
`orchestrator-agent → change-agent`

## Delegate to Subagents
change-judge → code-review-agent → security-agent (`guarded` only) → decision-ledger-writer → audit-trail-writer → harness-updater

## Execution order
```
load manifest + plan (plan-as-input)
 → GATE: refuse unless rule 40 pre-code gate for workflow.selected is met
 → FRESHNESS: python tools/context/refresh.py --check (every service); refuse if manifest files changed since
             task.commit, or the manifest has no seeds.semantic_search.ran: true (rebuild it with /build-context)
 → tests first (characterisation for touched uncovered symbols, failing tests for ACs)
 → implement plan steps (manifest files only; scope drift → stop, back to /build-context)
 → /refresh-context <id> --tests   (refresh.py --stale --tests, then manifest.py --verify-scope <id>;
                                    exit 4 = scope grew → scope-change request via --amend before validating)
 → run workflow.required_checks → verification.md (include the refresh snapshot + scope check)
 → change-judge + code-review-agent (+ security-agent if guarded)
 → repair loop from findings only (max 3) → needs_human; every repair edit → /refresh-context <id> again
 → decision-ledger-writer → python tools/context/record_episode.py <id> --outcome … --lessons "…"
 → CLOSE GATE: python tools/context/refresh.py --check   (exit 0: nothing changed since the last refresh;
                                                            exit 2 → /refresh-context again, then re-validate)
```

## Enforce Rules
00, 02, 05, 07, 09, 10, 22, 23, 40

## Use Templates / Skills
`.claude/skills/brownfield-context/SKILL.md`, `.claude/skills/plan-as-input/SKILL.md`,
`.claude/templates/decision-ledger-template.md`, `.claude/templates/code-review-template.md`,
`.claude/templates/test-results-template.md`, `.claude/templates/audit-trail-template.md`

## Execution Policy
Plan → Act → Validate → Refine, max 3. Stop when iteration 1 Validate passes.

## Clarification Protocol
Unknowns the plan does not resolve → stop that step, ask, record in the ledger. Never guess business behaviour.

## Command-Specific Hardening
- **Refuse** when: no manifest; plan not `Ready`; workflow `analyze-only` or `clarify`; approval missing for
  `plan-approve-execute`/`guarded`; primary service not in `brownfield.enabled_services`; manifest stale.
- Only manifest `files` + their tests may change (change-judge enforces).
- Contracts regenerate only when the plan says so (the repo's contract tool, then `brownfield.checks.contracts`).
- Never weaken tests, coverage gates, or contracts to pass.

## Definition of Done
- [ ] Gate honoured (or refused with reason)
- [ ] Tests for every AC; characterisation tests for touched uncovered symbols
- [ ] All `workflow.required_checks` green, incl. impacted services' suites; e2e when cross-service
- [ ] change-judge PASS; code review no blocking findings; security PASS when guarded
- [ ] `/refresh-context` after the last edit: exit 0, scope check within scope (or amended); `refresh.py --check` exit 0 at close
- [ ] `verification.md`, completed `decision-ledger.md`, episode appended
- [ ] `artifacts/audit/<date>-implement-change-<id>.md`; harness updated

## Required Output
Code + tests; `artifacts/changes/<id>/verification.md`; ledger; `artifacts/memory/episodes.jsonl` line; audit.

## Next command

> ✅ `/implement-change` complete — `<id>` judged **PASS**, checks green, episode recorded.
> **Next command:** human diff review, then `/evaluate-change <id>` (final scorecard), then `/review-changes`
> (release readiness) or the next `/build-context`.
