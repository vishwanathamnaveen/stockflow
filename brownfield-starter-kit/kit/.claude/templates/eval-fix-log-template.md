# Eval Fix Log — {{RUN_OR_SPRINT}}

> Tracks `/close-eval-gaps` walk. Never auto-fix items with `auto_fix: false`.

| Field | Value |
|-------|-------|
| **Fix queue source** | `evals/product/results/{{date}}-fix-queue.json` |
| **Orchestrator run** | {{timestamp}} |
| **Iteration** | {{n}} of 3 |

## Queue summary

| Status | Count |
|--------|-------|
| open | |
| in_progress | |
| closed | |
| needs_human | |

## Items processed

| fix_id | case_path | owning_agent | auto_fix | attempts | status | agent run audit |
|--------|-----------|--------------|----------|----------|--------|-----------------|
| | | backend-agent | true | 1 | closed | |

## Delegation log

| Timestamp | Agent | Action | Result |
|-----------|-------|--------|--------|
| | | re-delegate with feedback | |

## Escalations (attempt ≥ 3)

| fix_id | Reason | Human action required |
|--------|--------|----------------------|
| | | |

## Re-eval results

| case_path | Before | After | Ledger ref |
|-----------|--------|-------|------------|
| | fail | pass | |

**Output path:** `artifacts/audit/{{date}}-close-eval-gaps-{{task}}.md` (append or companion `evals/product/results/{{date}}-fix-log.md`)
