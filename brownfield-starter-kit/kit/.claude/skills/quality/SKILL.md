---
name: quality-coordination
description: Coordinate expand, run-tests, and run-eval. Ensure the local stack is up before E2E. Route failures to owning agents via close-eval-gaps. Never lower gates or self-approve test packages.
---

# Quality coordination

quality-agent coordinates `/expand-test-coverage`, `/run-tests`, and `/run-eval`. test-agent writes cases and matrix; br-coverage-validator is the only writer of `docs/test-cases-br-coverage.md`.

## Expand (`/expand-test-coverage`)

1. Intake-normalizer when sources are untrusted (skill: `intake-safety`).
2. test-case-generator → `docs/test-cases.md` + `docs/test-matrix.md`.
3. br-coverage-validator → `docs/test-cases-br-coverage.md` (**PASS** required).
4. Write `docs/quality/test-package-review.md` as **Pending Approval** — stop; human approves before `/run-tests`.

## Run tests (`/run-tests`) — application must be running

**Before any Playwright or live API probe:**

```bash
export API_MODULE_ROOT="<from config modules.api>"
export UI_MODULE_ROOT="<from config modules.ui>"
bash scripts/run-local-stack.sh
bash scripts/verify-stack-health.sh
```

If verify fails: record **environment FAIL** in `artifacts/test-results-<date>.md`; route API boot issues to **backend-agent**, UI boot to **frontend-agent**; do not mark journeys as pass.

**Execution order:** JUnit/IT → Vitest → Playwright (see skill: `playwright-e2e`, `jacoco-coverage`, `br-coverage`).

On test failure: e2e-defect-analyzer writes `artifacts/issues/<date>-e2e-failure.md` with **owning_agent** (backend-agent | frontend-agent | api-agent).

## Eval (`/run-eval` + `/close-eval-gaps`)

1. eval-agent → completeness ledger + `fix-queue.json`.
2. Orchestrator walks `/close-eval-gaps` for items with `auto_fix: true`.
3. Delegate each open item to **owning_agent** (see skill: `eval-suite`).
4. Re-run affected eval cases; max 3 attempts per item.
5. Human receives: green tests + verified stack + ledger with no open P0/P1 auto_fix items.

## Must NOT

- Self-approve test packages or lower coverage floors.
- Run `/run-tests` before package **Approved** and br-coverage **PASS**.
- Skip stack verify before E2E.
- Treat silence (no case, skipped safety family) as pass on eval.

## Subagents

`br-coverage-validator`, `eval-agent`, `coverage-analyzer`, `e2e-defect-analyzer`, `playwright-self-healer`
