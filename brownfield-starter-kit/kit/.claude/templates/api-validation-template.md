# API Validation Report — {{SCOPE}}

> Live probe results from `/validate-api-endpoints`. Positives and mandatory negatives required. No fabricated counts.

| Field | Value |
|-------|-------|
| **Run ID** | APIVAL-{{YYYYMMDD}}-{{slug}} |
| **Date (UTC)** | {{timestamp}} |
| **Base URL** | {{url}} (localhost/staging only — never third-party production) |
| **Environment** | local / staging |
| **Command** | `/validate-api-endpoints` |
| **Agent** | test-agent (mode live) |
| **OpenAPI ref** | `contracts/openapi/{{file}}.yaml` |
| **Story / FR scope** | {{ids}} |

## Summary

| Metric | Value |
|--------|-------|
| Operations probed | |
| Pass | |
| Fail | |
| Skipped (with reason) | |
| **Verdict** | Ready / Conditional / Not ready |

## Preconditions

- Auth token source: {{env var name — value redacted}}
- Test data setup:
- Known limitations:

## Probe matrix

| operationId | Method | Path | case_id | type (+/-) | HTTP expected | HTTP actual | Pass | Notes |
|-------------|--------|------|---------|------------|---------------|-------------|------|-------|
| | POST | | TC- | positive | 201 | | | |
| | POST | | TC- | negative | 400 | | | |
| | GET | | TC- | negative (401) | 401 | | | |

## Failures (detail)

### {{operationId}} — {{case_id}}

- **Expected:**
- **Actual:**
- **Response body (redacted):**
- **Likely layer:** controller / service / auth / validation
- **BRD / OpenAPI ref:**
- **Recommended owner:** backend-agent / api-agent

## Security checks

| Check | Result | Evidence |
|-------|--------|----------|
| Unauthenticated access blocked on protected routes | | |
| Invalid token rejected | | |
| No secrets in logs/evidence | | |

## Traceability

| case_id | rule_ids (FR/BR) | test-cases.md section |
|---------|------------------|------------------------|
| | | |

## Open items

| ID | Description | Owner | Blocking |
|----|-------------|-------|----------|
| DQ- | | | yes/no |

**Output path:** `docs/quality/api-validation/{{date}}-{{slug}}.md` or `artifacts/api-validation/{{date}}-{{slug}}.md`
