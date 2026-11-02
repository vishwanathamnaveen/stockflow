# KPI Executive Summary — Sprint <sprint_number> — <run_id>

## Metadata

| Field | Value |
|-------|-------|
| Run ID | <run_id> |
| Generated (UTC) | <timestamp> |
| Stacks assessed | java / nextjs / both |
| Overall verdict | GO / GO_WITH_CONDITIONS / NO_GO |

## Scorecard summary (0–10)

### Backend — <modules.api>

**Backend Overall:** <backend_overall> / 10

| Metric | Score |
|--------|-------|
| Security | <n>/10 |
| Readability | <n>/10 |
| Requirement coverage | <n>/10 |
| Test coverage | <n>/10 |
| Defect density | <n>/10 |
| Maintainability | <n>/10 |
| Adherence to guidelines | <n>/10 |
| Documentation | <n>/10 |

### UI — <modules.ui>

**UI Overall:** <ui_overall> / 10

| Vector | Score |
|--------|-------|
| Path Traversal | <n>/10 |
| Credential Exposure | <n>/10 |
| Outdated Dependencies | <n>/10 |
| Fail Rate Prevention | <n>/10 |
| Maturity Index | <n>/10 |
| Structural Weakness | <n>/10 |
| Verbosity/Complexity | <n>/10 |
| Unused Package | <n>/10 |
| Implicit Exploitation | <n>/10 |
| JSON Key / Null Pointer | <n>/10 |
| Assumption Design Debt | <n>/10 |

## At a Glance

| Stack | Module | Overall score | Status | Critical blockers | Top risk |
|-------|--------|---------------|--------|-------------------|----------|
| Java | <module> | <backend_overall>/10 | G/A/R | | |
| Next.js | <app> | <ui_overall>/10 | G/A/R | | |

## Enterprise KPI Rollup (worst status per KPI across stacks)

| KPI ID | KPI Name | Java | Next.js | Combined status |
|--------|----------|------|---------|-----------------|
| KPI-01 | Security | | | |
| KPI-02 | Test Coverage | | | |
| KPI-03 | Requirement Coverage | | | |
| KPI-04 | Defect Density | | | |
| KPI-05 | Maintainability | | | |
| KPI-06 | Code Readability | | | |
| KPI-07 | Adherence to Guidelines | | | |
| KPI-08 | Documentation | | | |
| KPI-09 | Dependency Health | | | |
| KPI-10 | Reliability & Error Handling | | | |
| KPI-11 | Observability Maturity | | | |
| KPI-12 | Performance Readiness | | | |

## Critical Blockers (release impact)

1.

## Conditions and Waivers

| KPI | Condition | Owner | Target date |
|-----|-----------|-------|-------------|
| | | | |

## Recommendations (prioritized)

1.

## Validation Summary

- Deterministic evidence collected from standard toolchain (not custom heuristic scripts).
- Suitable for sprint handoff and `release-agent` (mode readiness) input.
