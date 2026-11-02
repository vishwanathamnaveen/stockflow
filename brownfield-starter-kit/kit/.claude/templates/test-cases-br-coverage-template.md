# Test-case BR Coverage — {{SCOPE}}

> Validates `docs/test-cases.md` against `evals.rule_source` (Accepted BRD or story pack). **PASS required before scripts or execution.** Written **only** by **br-coverage-validator** (quality-agent). Implementers must not stamp PASS.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint, release, slice}} |
| **Rule source** | {{path to Accepted BRD or story pack}} |
| **Cases file** | `docs/test-cases.md` |
| **Matrix file** | `docs/test-matrix.md` |
| **Scorer** | br-coverage-validator |
| **Date** | {{YYYY-MM-DD}} |
| **Status** | **PASS** / **FAIL** / **BLOCKED** |
| **Coverage ratio** | mapped / in-scope (percent) |

## Coverage rules

- Every in-scope FR/BR has ≥1 `case_id` or an explicit **gap** row.
- A missing case is **gap**, not covered. **Silence is FAIL.**
- P0/P1 gaps cannot be waived by test-agent.
- If Status is **FAIL**: expand `docs/test-cases.md`, re-score. Do **not** write `docs/quality/test-package-review.md` as Pending Approval. Do **not** write gap scripts or run `/run-tests`.

## Coverage matrix

| rule_id | cited statement (short) | priority | case_ids | status | notes |
|---------|-------------------------|----------|----------|--------|-------|
| FR-001 | | P0/P1/P2 | TC-001, TC-002 | covered / gap | |
| BR-001 | | | | gap | DQ- if intentional defer |

## Roll-up

| Priority | Total rules | Covered | Gaps | Coverage % |
|----------|-------------|---------|------|------------|
| P0 | | | | must be 100% for PASS |
| P1 | | | | |
| P2 | | | | |
| **All in-scope** | | | | |

## Gaps requiring action

| rule_id | gap reason | Owner | Target date | Blocking scripts |
|---------|------------|-------|-------------|------------------|
| | no negative case | test-agent | | yes |

## Validator attestation

| Check | Result |
|-------|--------|
| All P0 covered or waived with decision | |
| All P1 covered or documented gap | |
| case_ids exist in test-cases.md | |
| No orphan cases without rule_ids | |

**Output path:** `docs/test-cases-br-coverage.md`
