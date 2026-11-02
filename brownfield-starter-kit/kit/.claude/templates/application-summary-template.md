# Application Summary — {{PROJECT_OR_RELEASE}}

> Executive-ready summary from `/application-summary`. Metrics must be fresh (collected this run), not stale or invented.

| Field | Value |
|-------|-------|
| **Generated** | {{YYYY-MM-DD HH:MM UTC}} |
| **Command** | `/application-summary` |
| **Agent** | documentation-agent (mode summary) |
| **Commit / branch** | {{sha}} / {{branch}} |
| **Sprint / release** | {{id or N/A}} |
| **Plan status** | Approved / N/A |

## Executive summary

- **What was delivered:** (2–4 sentences, cite story/SP ids)
- **Pipeline stage reached:** (from `docs/harness/progress.md`)
- **Overall readiness:** Ready for PR / Ready for release review / Blocked

## Scope delivered

| Story / SP | Title | API | UI | Tests | Status |
|------------|-------|-----|----|----|--------|
| | | yes/no | yes/no | yes/no | Done / Partial |

## Architecture snapshot

- **Modules touched:** `${modules.api}`, `${modules.ui}`, etc.
- **Contracts:** `contracts/openapi/…`
- **Migrations:** (version ids or N/A)
- **Key integrations:**

## Quality evidence (fresh metrics)

| Area | Metric | Threshold | Actual | Source artifact |
|------|--------|-----------|--------|-----------------|
| Unit coverage (API) | line % | config floor | | JaCoCo / coverage report |
| UI unit tests | pass/fail | | | npm test output |
| E2E | pass/fail | | | `artifacts/e2e-test-results-*.md` |
| BR coverage | PASS/FAIL | PASS | | `docs/test-cases-br-coverage.md` |
| KPI validation | GO/NO_GO | | | `docs/quality/kpi-validations/` |
| Security scan | critical/high open | 0 unwaived | | `artifacts/security/` |
| Code review | blocking findings | 0 | | `artifacts/code-reviews/` |

## Known gaps and risks

| ID | Gap / risk | Severity | Owner | Mitigation |
|----|------------|----------|-------|------------|
| DQ- | | | | |

## Human gates status

| Gate | Status | Reference |
|------|--------|-----------|
| BRD Accepted | | |
| Plan Approved | | |
| KPI GO | | |

## Recommended next steps

1. 
2. 

**Next command:** `/application-summary` | `/application-summary` | `/plan-sprint`

**Output path:** `docs/application-summary-{{date}}.md` or `artifacts/application-summary-{{date}}.md`
