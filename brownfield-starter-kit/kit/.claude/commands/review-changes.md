# /review-changes

## Objective

Code, test, and security review of the slice. Read-only review agent. Does **not** run eval-agent — that is `/run-eval`.

## Runtime Inputs

### Required

- diff scope
- test evidence (`artifacts/test-results-*.md`)
- `evals/product/results/<date>-completeness-ledger.md` from `/run-eval`
- Open `auto_fix: true` items closed or `needs_human` (walk `/close-eval-gaps` via `/run-eval` first)

### Optional

- test-matrix
- STATUS.md
- `governed_plan` / `sprint_governed_plan`

## Plan-as-input mode

When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Clarification Protocol.

## Use Agents

orchestrator-agent → code-review-agent + security-agent

## Delegate to Subagents

security-reviewer, coverage-analyzer, br-coverage-validator, audit-trail-writer

Do **not** invoke eval-agent.

## Enforce Rules

02, 03, 07, 09, 10, 15, 21, 23

## Use Templates

review-findings-template.md, code-review-template.md, audit-trail-template.md, plan-act-validate-refine-loop.md

## Required Output

- artifacts/audit/<date>-review-changes.md

## Command-Specific Hardening

Do not merge into quality-agent. Do not invoke eval-agent. Remaining P0/P1 safety items on the latest completeness ledger force Block. Family with zero cases on that ledger is Block, not Approve. Missing completeness ledger → **refuse**; advise `/run-eval` first. Missing or FAIL `docs/architecture/stack-conventions.md` when Java API/tests changed (or `artifacts/templates/*-vars.yaml` exists) is Block.

## Execution Policy

Loop: Plan → Act → Validate → Refine. Max 3 is a ceiling. Iteration 1 Validate pass → stop. Refine only from findings. Escalate with owners after iteration 3.

## Clarification Protocol

After resolve-before-ask, register Open DQ when the completeness ledger is missing. Do not invent eval results. Still refuse when `/run-eval` has not run. Do not STOP for a clarification round except human gates (BRD Accepted, plan Approved, test-package Approved).

## Artifact Persistence

Canonical paths above plus `artifacts/audit/<date>-<command>-<task>.md`. Metadata: timestamp, iteration, validation summary.

## Definition of Done

- [ ] Severity findings
- [ ] P0/P1 remaining → Block
- [ ] reviewer did not mutate source
- [ ] `docs/test-cases-br-coverage.md` Status **PASS** or Blocking gaps listed (implementers must not stamp PASS). Cases + matrix required; UAT catalog optional
- [ ] Completeness ledger from `/run-eval` present; always-on safety families present
- [ ] Stack-conventions compliance noted in audit when API/tests changed
- [ ] `artifacts/audit/<date>-review-changes.md` written
- [ ] Harness updated (phase-changing)

## Next command

```
✅ /review-changes complete.
**Next command:** `/application-summary` if Approve; otherwise owning agents fix findings and re-run `/review-changes`. If auto_fix items are open, complete `/run-eval` and `/close-eval-gaps` first. Security scan evidence packs are not in this kit.
```
