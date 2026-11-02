# E2E Test Results — {{SCOPE}}

> Playwright (or configured runner) evidence from `/implement-ui` or test-agent. Real counts only.

| Field | Value |
|-------|-------|
| **Run ID** | E2E-{{YYYYMMDD}}-{{slug}} |
| **Timestamp (UTC)** | {{timestamp}} |
| **Environment** | local / CI |
| **Branch / commit** | {{branch}} / {{sha}} |
| **UI module root** | `${modules.ui}` |
| **Command** | {{/implement-ui, /expand-test-coverage}} |
| **Runner** | `npm run test:e2e` (see playwright-e2e skill) |

## Summary

| Metric | Value |
|--------|-------|
| Spec files | |
| Tests total | |
| Passed | |
| Failed | |
| Skipped | |
| Flaky (if tracked) | |
| Duration | |
| **Verdict** | Pass / Fail / Blocked |

## Environment notes

- **Browser:** chrome channel / {{browser}}
- **Base URL:** {{url}}
- **Auth setup:** (fixture name — no credentials in log)

## Results by spec

| Spec file | Tests | Pass | Fail | Skip | Linked AC / TC |
|-----------|-------|------|------|------|----------------|
| `e2e/specs/…` | | | | | |

## Failures (detail)

### {{spec}} — {{test name}}

- **AC / TC ref:**
- **Error:**
- **Screenshot / trace:** `playwright-report/…` (path only)
- **Suggested owner:** frontend-agent / test-agent

## Traceability

| TC ID | Spec | Status |
|-------|------|--------|
| | | pass/fail/not run |

## Open items

| ID | Item | Owner |
|----|------|-------|
| | | |

**Output path:** `artifacts/e2e-test-results-{{date}}.md`
