# Code Review — {{SCOPE}}

> Read-only review from `/review-changes` or code-review-agent. Mutations belong in a separate implement/fix pass.

| Field | Value |
|-------|-------|
| **Review ID** | CR-{{YYYYMMDD}}-{{slug}} |
| **Date** | {{YYYY-MM-DD}} |
| **Reviewer** | code-review-agent |
| **Scope** | {{PR, sprint slice, files}} |
| **Base ref** | {{branch / commit range}} |
| **Story / AC refs** | {{ids}} |

## Summary

| Verdict | Blocking count | Advisory count | Notes |
|---------|----------------|----------------|-------|
| Approve / Request changes / Block | | | |

## Findings

| ID | Severity | Category | Location | Finding | Recommendation | AC/FR ref |
|----|----------|----------|----------|---------|----------------|-----------|
| CR-1 | blocking / advisory | correctness / security / maintainability / tests / governance | `path:line` | | | |

### Severity definitions

| Level | Meaning |
|-------|---------|
| **blocking** | Must fix before merge — security, wrong business behavior, missing tests for critical path |
| **advisory** | Should fix — style, minor refactor, non-critical gaps |

## Standards checked

| Standard | Result | Notes |
|----------|--------|-------|
| Matches approved plan / AC | | |
| No invented business behavior | | |
| Error handling / envelope | | |
| No secrets in code | | |
| Test coverage for changed logic | | |
| Scope.yaml honored | | |
| Migration forward-only | | |

## Positive observations

-

## Open questions for author

| ID | Question | Owner |
|----|----------|-------|
| DQ- | | |

**Output path:** `artifacts/code-reviews/{{date}}-{{slug}}.md`
