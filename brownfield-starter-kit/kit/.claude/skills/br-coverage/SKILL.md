---
name: br-coverage
description: Ensure 100% FR/BR coverage in designed cases and Done matrices. Use during plan, implement-*, expand-test-coverage, run-tests, run-eval, review.
---

# BR Coverage Skill

## When
Any delivery/quality command that designs or scores tests.

## Steps
1. Load `evals.rule_source` (Accepted BRD or story pack) or the SP item’s cited FR/BR.
2. **Design** — `automation-companion-author` / `test-case-generator` writes `docs/test-cases.md` (expand-test-coverage Phase 1). `tc-traceability-mapper` writes `docs/test-matrix.md` (Phase 1b). Do **not** generate a UAT catalog.
3. **Coverage gate** — quality-agent delegates br-coverage-validator (`pre-script`). Only writer of `docs/test-cases-br-coverage.md` (includes coverage ratio). FAIL → expand cases; do **not** `/run-tests`. Missing cases or matrix = FAIL. Missing frozen UAT catalog is not FAIL.
4. **Human package** — on PASS, `docs/quality/test-package-review.md` is **Pending Approval**. Agents Must NOT self-approve.
5. **Scripts/runs** — `/run-tests` only after Status **PASS** and package **Approved** (not implement-api/ui slice tests — ASSUMPTION-PCC-002).
6. Diff against OpenAPI operations, service methods, UI actions, tests.
7. Mark Status; Block only with owner+reason.
8. Cite at least one automated test ID/class per Tested BR condition/constraint when Automated ≠ NONE.

## Anti-patterns
- Writing or running `/run-tests` scripts before BR coverage PASS and human package Approved.
- Implementers stamping PASS on `docs/test-cases-br-coverage.md`.
- Treating the matrix as sufficient without case bodies (steps + expected).
- Generating or refreshing `docs/test/manual/**` on expand.
- Blanket "covered by ApiIT" for hundreds of BRs without row-level citations.
- Marking Blocked as Tested to inflate requirement coverage.
