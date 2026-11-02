# Phase Gate — {{PHASE_NAME}}

> Checkpoint before advancing pipeline. Human gates cannot be self-approved by agents.

| Field | Value |
|-------|-------|
| **Gate ID** | GATE-{{phase}} |
| **Phase** | Intake / Plan / Execute / Quality / Release |
| **Date** | {{YYYY-MM-DD}} |
| **Command completed** | {{/command}} |
| **Status** | Pass / Fail / Waived |
| **Approver (if human gate)** | {{role — not agent}} |

## Entry criteria

| Criterion | Required | Met | Evidence |
|-----------|----------|-----|----------|
| Prior phase Done in harness | yes | | `docs/harness/progress.md` |
| Required artifacts exist | yes | | paths |
| Human gate satisfied | if applicable | | decisions.md |

## Exit criteria (Definition of Done)

| # | Check | Result | Evidence path |
|---|-------|--------|---------------|
| 1 | Command DoD complete | | audit |
| 2 | Tests / evals per command | | |
| 3 | Open P0 items | none | |

## Human gates at this phase

| Gate | Status | Waiver in decisions.md |
|------|--------|------------------------|
| BRD Accepted | | |
| Plan Approved | | |
| fix plan proceed | N/A in this kit | |
| Cutover sign-off | | |

## Blockers

| ID | Blocker | Owner | ETA |
|----|---------|-------|-----|
| DQ- | | | |

## Decision

- **Proceed to next command:** `/{{next}}`
- **Or stop reason:**

**Output path:** Record in `artifacts/audit/{{date}}-{{command}}-{{task}}.md` and update harness via harness-updater
