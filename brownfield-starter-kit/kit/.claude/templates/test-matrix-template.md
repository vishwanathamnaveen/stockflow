# Test Matrix — {{SCOPE}}

> Index only — case bodies live in `docs/test-cases.md`. br-coverage-validator scores against this index + case file.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint, slice, release}} |
| **Cases file** | `docs/test-cases.md` |
| **Coverage file** | `docs/test-cases-br-coverage.md` |
| **Last updated** | {{YYYY-MM-DD}} |

## Matrix

| case_id | title | rule_ids (FR/BR) | AC | layer | type (+/-) | status | script_path | last_result |
|---------|-------|------------------|----|-------|------------|--------|-------------|-------------|
| TC-001 | | FR- / BR- | AC- | unit/IT/e2e | positive/negative | designed/scripted/pass/fail | | |

## Status definitions

| Status | Meaning |
|--------|---------|
| designed | In test-cases.md; no script yet |
| scripted | Automation exists |
| pass / fail | Last run result |

## Roll-up

| Layer | Designed | Scripted | Pass |
|-------|----------|----------|------|
| unit | | | |
| IT | | | |
| e2e | | | |

## Rules

- Do not add rows without a matching section in `docs/test-cases.md`.
- Do not mark pass without a test-results artifact.
- Coverage PASS required before scripting new rows.

**Output path:** `docs/test-matrix.md`
