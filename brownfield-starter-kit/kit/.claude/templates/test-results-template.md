# Test Results — {{SCOPE}}

> Normalized runner output from test-agent or implement commands. Real counts, env, timestamp — no fabrication.

| Field | Value |
|-------|-------|
| **Run ID** | TR-{{YYYYMMDD}}-{{slug}} |
| **Timestamp (UTC)** | {{timestamp}} |
| **Environment** | local / CI |
| **Branch / commit** | {{branch}} / {{sha}} |
| **Command** | {{/implement-api, /expand-test-coverage, etc.}} |
| **Agent** | test-agent / backend-agent / frontend-agent |

## Summary

| Suite | Command | Total | Pass | Fail | Skip | Duration | Verdict |
|-------|---------|-------|------|------|------|----------|---------|
| API unit | `mvn test` / pytest | | | | | | |
| API IT | | | | | | | |
| UI unit | `npm test` | | | | | | |
| E2E | `npm run test:e2e` | | | | | | see e2e template |

## Coverage (if collected)

| Module | Line % | Branch % | Floor | Met |
|--------|--------|----------|-------|-----|
| API | | | config | yes/no |
| UI | | | | |

## Failures

| Test | Class / spec | TC ref | Error (summary) | Owner |
|------|--------------|--------|-----------------|-------|
| | | | | |

## Traceability

| TC ID | rule_ids | Automated test path | Result |
|-------|----------|---------------------|--------|
| | FR-/BR- | | pass/fail |

## Artifacts

| Type | Path |
|------|------|
| Surefire / pytest log | |
| JaCoCo / coverage | |
| Playwright report | |

**Output path:** `artifacts/test-results-{{date}}.md`
