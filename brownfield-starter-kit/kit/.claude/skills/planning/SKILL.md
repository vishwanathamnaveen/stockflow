---
name: planner
description: Turn Accepted BRD into sprint plan with implement-* execute rows only. Use on /plan-sprint with plan-as-input skill.
---

# Planning

## When

`/plan-sprint` after BRD **Accepted** (or waiver in `docs/harness/decisions.md`).

## Procedure

1. Load skill `plan-as-input` when `@brd` or `@sprint_plan` supplied.
2. Apply `sprint-plan-template.md` → `artifacts/sprints/<id>-plan.md`.
3. Internal gap step → `artifacts/sprints/<id>-gap-report.md` (not a public command).
4. Execute rows **only**: `/implement-api` → `/implement-ui` → `/expand-test-coverage` → `/run-tests` → `/run-eval` → `/review-changes` → `/application-summary`.
5. Status: **Proposed — Pending Approval** until human approves.

## Must NOT

- Emit generate-backend, generate-frontend, or wire commands as plan steps.
- Self-approve the plan or start implement-* before Approval.

## Subagents

`sprint-planner`, `requirement-traceability-mapper`, `gap-identifier`, `open-questions-cataloger`
