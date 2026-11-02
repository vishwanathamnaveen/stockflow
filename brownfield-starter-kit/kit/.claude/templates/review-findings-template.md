# Review Findings — {{SCOPE}}

> Consolidated output from `/review-changes` (code-review-agent + security-agent + eval-agent).

| Field | Value |
|-------|-------|
| **Review ID** | REV-{{YYYYMMDD}}-{{slug}} |
| **Date** | {{YYYY-MM-DD}} |
| **Scope** | {{sprint slice, PR range}} |
| **Commands in scope** | implement-api, implement-ui, expand-test-coverage |
| **Overall verdict** | Approve / Request changes / Block release |

## Executive summary

| Area | Blocking | Advisory | Notes |
|------|----------|----------|-------|
| Code quality | | | |
| Security | | | |
| Eval / factory safety | | | |
| **Total** | | | |

## Code review findings

| ID | Severity | Location | Finding | Recommendation | Owner |
|----|----------|----------|---------|----------------|-------|
| | blocking/advisory | | | | |

## Security findings

| ID | Severity | Category (OWASP) | Finding | Remediation | Owner |
|----|----------|------------------|---------|-------------|-------|
| | critical/high/medium/low | | | | security-agent |

## Eval results summary

| Eval family | Result | Completeness ledger |
|-------------|--------|---------------------|
| L1-04 input validation | pass/fail | |
| L1-05 error handling | | |
| L1-08 security anti-pattern | | |
| L1-09 secret handling | | |
| L4-03 gate blocks security | | |

**Ledger path:** `evals/product/results/{{date}}-completeness-ledger.md`

## Fix queue

| fix_id | owning_agent | auto_fix | status |
|--------|--------------|----------|--------|
| | | true/false | open/closed |

## Required actions before `/application-summary`

1. 
2. 

## Sign-off

| Reviewer type | Verdict | Date |
|---------------|---------|------|
| Code review | | |
| Security | | |

**Output path:** `artifacts/code-reviews/{{date}}-review-findings-{{slug}}.md`

**Next command:** `/application-summary` (if unblocked) or `/close-eval-gaps`
