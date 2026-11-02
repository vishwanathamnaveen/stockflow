# Requirement Traceability — {{SPRINT_OR_RELEASE}}

> Maps FR/BR/AC → design → implementation → test → evidence. Used by `/plan-sprint`, `/plan-sprint`, KPI-03.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint N, release, bounded context}} |
| **BRD / story pack** | {{path}} |
| **Status** | Draft / Complete |
| **Last updated** | {{YYYY-MM-DD}} |

## Forward traceability

| FR/BR/AC ID | Requirement summary | Design artifact | API (operationId) | UI (route/component) | Test case(s) | Status |
|-------------|----------------------|-----------------|-------------------|----------------------|--------------|--------|
| FR-001 | | tech-spec / OpenAPI | | | TC- | Not started / In progress / Done |

## Backward traceability (tests → requirements)

| Test case ID | Layer | rule_ids | Script path | Last run | Result |
|--------------|-------|----------|-------------|----------|--------|
| TC- | unit/IT/e2e | FR-/BR- | | | pass/fail |

## Coverage summary

| Metric | Count |
|--------|-------|
| Total in-scope FR/BR | |
| With ≥1 test case | |
| With passing automation | |
| Explicit gaps (documented) | |

## Gaps

| ID | rule_id | Gap description | Owner | Target sprint |
|----|---------|-----------------|-------|---------------|
| DQ- | | | | |

## Orphan detection

| Artifact | Path | Missing link to |
|----------|------|-----------------|
| | | FR/BR/AC |

**Output path:** `docs/sprint{{N}}/traceability-{{slug}}.md` or embedded in sprint plan
