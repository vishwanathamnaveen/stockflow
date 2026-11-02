# Test Strategy — {{PROJECT_OR_RELEASE}}

> Risk-based testing approach for sprint or release. Align with test-agent; do not invent scope.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint, release, bounded context}} |
| **BRD / story pack** | {{path}} |
| **Author** | test-agent / quality-agent |
| **Date** | {{YYYY-MM-DD}} |
| **Status** | Draft / Approved |

## Objectives

- **Quality goals:**
- **Risk drivers:**

## Scope of testing

| In scope | Out of scope |
|----------|--------------|
| | |

## Test levels

| Level | Purpose | Tools | Owner |
|-------|---------|-------|-------|
| Unit | Logic isolation | JUnit/pytest/Jest | backend/frontend-agent |
| Integration | API contracts, DB | MockMvc, Testcontainers | test-agent |
| E2E | User journeys | Playwright | test-agent |
| Live API probes | Staging validation | rest-api-endpoint-tester | test-agent |
| Security | SAST/DAST | security-agent | |
| Performance | Load (if NFR) | sre-agent | |

## Entry / exit criteria

| Phase | Entry | Exit |
|-------|-------|------|
| Test design | Approved plan, AC available | test-cases.md + matrix |
| Scripting | BR coverage PASS | Scripts for covered cases |
| Execution | CI green on main paths | test-results artifacts |
| Release | KPI GO, no open P0 | release-readiness |

## Risk matrix

| Risk area | Likelihood | Impact | Mitigation tests |
|-----------|------------|--------|------------------|
| AuthZ bypass | | | TC- (negative) |
| Data corruption | | | |
| UI regression | | | e2e |

## Environments

| Env | Purpose | Data policy |
|-----|---------|-------------|
| local | dev | synthetic |
| CI | gate | fixtures |
| staging | live probes | masked |

## Responsibilities

| Role | Responsibility |
|------|----------------|
| test-agent | cases, coverage gate, scripts |
| quality-agent | coordinate, KPI, evals |
| QA engineer | review generated Playwright (if applicable) |

## Metrics

| Metric | Target | Source |
|--------|--------|--------|
| BR coverage | PASS | test-cases-br-coverage.md |
| API line coverage | config floor | JaCoCo |
| Defect escape rate | org target | issue logs |

**Output path:** `docs/quality/test-strategy-{{slug}}.md`
