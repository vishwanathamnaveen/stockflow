# Traceability Matrix — {{SCOPE}}

> Cross-artifact index for stories, FR/BR, API, UI, tests. Used by `/generate-brd`, KPI-03.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint, feature, release}} |
| **Source pack** | {{story pack path}} |
| **Generated** | {{YYYY-MM-DD}} |
| **Status** | Draft / Complete |

## Master matrix

| Story / SP | FR/BR/AC | Gherkin / AC text (short) | OpenAPI op | UI route / component | DDL / entity | Test case(s) | Status |
|------------|----------|---------------------------|------------|----------------------|--------------|--------------|--------|
| SP-01 | AC-01 | | | | | TC- | designed / scripted / pass |

## Coverage roll-up

| Dimension | Total items | Linked | Gap count |
|-----------|-------------|--------|-----------|
| AC | | | |
| API operations | | | |
| UI screens | | | |
| Test cases | | | |

## Gaps (explicit)

| Gap ID | Missing link | Owner | Plan |
|--------|--------------|-------|------|
| DQ- | AC-05 has no e2e | test-agent | sprint N+1 |

## Orphans

| Artifact type | ID / path | Issue |
|---------------|-----------|-------|
| Test | TC-99 | no AC ref |

**Output path:** `docs/sprint{{N}}/traceability-matrix.md` or section in techno-functional pack
