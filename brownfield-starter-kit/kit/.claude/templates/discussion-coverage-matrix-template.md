# Discussion Coverage Matrix — {{BRD_OR_INTAKE}}

> Maps transcript/discussion topics to BRD sections. Used by `/generate-brd`. Every topic row must land in a section or Open DQ.

| Field | Value |
|-------|-------|
| **Source** | {{transcript path, meeting id}} |
| **BRD draft** | {{path}} |
| **Date** | {{YYYY-MM-DD}} |
| **Agent** | requirements-agent |

## Topic coverage

| Topic (from discussion) | Timestamp / locator | BRD section | FR/BR/DQ ID | Status | Notes |
|-------------------------|---------------------|-------------|-------------|--------|-------|
| | 00:12:34 | §5 FR | FR-001 | captured | |
| | | §14 Open Q | DQ-001 | open | needs SME |

## Section completeness

| BRD § | Section name | Topics expected | Topics captured | Gap |
|-------|--------------|-----------------|-----------------|-----|
| 5 | Functional requirements | | | |
| 6 | Business rules | | | |
| 14 | Open questions | | | |

## Uncovered topics (must become DQ or FR)

| Topic | Why uncovered | DQ ID | Owner | Blocking |
|-------|---------------|-------|-------|----------|
| | ambiguous | DQ- | | yes/no |

## Sign-off readiness

- [ ] Every discussion topic mapped or explicitly deferred with DQ
- [ ] No silent omissions
- [ ] Status remains **Draft — Pending Domain Review**

**Output path:** Section 13 of BRD or `artifacts/brd/{{date}}-discussion-coverage.md`
