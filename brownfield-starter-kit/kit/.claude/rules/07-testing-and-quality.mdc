---
description: Testing and quality
alwaysApply: true
---

# Testing and Quality

- Map tests to FR/BR or story AC IDs — not to informal chat.
- Write `docs/test-cases.md` (case bodies with full steps + expected) **and** `docs/test-matrix.md` (index). **br-coverage-validator** is the only writer of `docs/test-cases-br-coverage.md`.
- Classify BR Type with `.claude/templates/br-tc-taxonomy.md` before authoring negatives.
- **PASS + human Approved** (`docs/quality/test-package-review.md`) required before `/run-tests`.
- Slice tests on `/implement-api` and `/implement-ui` still require br-coverage PASS before that slice's scripts when scripts are generated.
- Line coverage floor from `config.yaml` `quality_gates.api_unit_line_coverage_min`.
- Positive and mandatory negative API cases (taxonomy: Constraint and Condition-gate).
- Eval-agent runs only via `/run-eval`. Cannot waive P0/P1.
- `/review-changes` requires a `/run-eval` completeness ledger.
- Untrusted intake must pass `scripts/intake-safety-scan.py` before case authoring.
