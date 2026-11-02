# Eval Results — {{RUN_ID}}

> From eval-agent (`/run-eval`). Completeness ledger required — silence is not a pass.

| Field | Value |
|-------|-------|
| **Run ID** | {{run_id}} |
| **Date (UTC)** | {{timestamp}} |
| **Mode** | incremental / full |
| **Commit** | {{sha}} |
| **Command** | {{parent command}} |
| **Agent** | eval-agent |

## Summary

| Metric | Value |
|--------|-------|
| Cases executed | |
| Pass | |
| Fail | |
| Skipped (with reason) | |
| **Overall** | Pass / Fail |

## Always-on safety families (required)

| Family | Case path | Result | Notes |
|--------|-----------|--------|-------|
| L1-04 input validation | | pass/fail | |
| L1-05 error handling | | pass/fail | |
| L1-08 security anti-pattern | | pass/fail | |
| L1-09 secret handling | | pass/fail | |
| L4-03 gate blocks security | | pass/fail | |

## Case results

| case_path | Grader | Result | owning_agent | auto_fix | fix_id |
|-----------|--------|--------|--------------|----------|--------|
| evals/product/wave-1/… | | pass/fail | backend-agent | true | |

## Completeness ledger

**Path:** `evals/product/results/{{date}}-completeness-ledger.md`

| Family | Expected | Executed | Silent skip? |
|--------|----------|----------|--------------|
| | | | must be NO |

## Fix queue updates

**Path:** `evals/product/results/{{date}}-fix-queue.json`

| fix_id | status | attempts |
|--------|--------|----------|
| | open/closed/needs_human | |

**Next command if auto_fix open:** `/close-eval-gaps`

**Output path:** `evals/product/results/{{date}}-eval-results.md`
