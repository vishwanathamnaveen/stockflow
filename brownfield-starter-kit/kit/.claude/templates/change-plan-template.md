# Change plan — {{TASK_ID}}

| Field | Value |
|---|---|
| **Status** | {{Ready \| Clarify}} |
| **Approval** | {{Not required (fast-track) \| Pending — human sets `Approved by <name> <YYYY-MM-DD>`}} |
| **Workflow** | {{workflow.selected}} — {{workflow.reason}} |
| **Confidence / Risk** | {{confidence.overall}} / {{risk.level}} ({{risk.score}}) |
| **Primary service** | {{services.primary}} (enabled: {{services.execution_enabled}}) |
| **Impacted services** | {{services.impacted}} |
| **Manifest** | `artifacts/changes/{{TASK_ID}}/context-manifest.yaml` @ `{{task.commit}}` |

> {{task.objective}}

## Change nature

{{additive | behavioural | breaking}} — {{one paragraph: what changes for callers, event consumers and stored data. Cite manifest sections.}}

## Acceptance criteria

| AC | Statement | Source |
|---|---|---|
| AC-1 | {{quoted from task, or ASSUMPTION-<id>}} | {{task.md / BR-xxx / ASSUMPTION}} |

## Steps (only manifest files)

| # | File | Change | Cites |
|---|---|---|---|
| 1 | {{tests file}} | characterisation / failing test for AC-1 | tests.uncovered_symbols / AC-1 |
| 2 | {{file}} | {{change}} | dependencies.direct[...] |

## Consumers and compatibility

| Service | Channel | Effect | Action |
|---|---|---|---|
| {{consumer service}} | {{rest GET /<resource>/{id}}} | {{none — additive field}} | {{run that service's suite}} |

## Data and rollout

- Migration: {{none \| reset local DBs \| migration script}} (manifest `data.notes`)
- Contracts: {{regenerate the OpenAPI contract with the repo's own tool; check with `brownfield.checks.contracts`}} / events.yaml payload update
- Flags: {{flag gating, if any}}

## Required checks

{{workflow.required_checks as a checklist}}

## Unknowns resolved / deferred

| Id | Resolution | Owner |
|---|---|---|
| U-1 | {{answer + source, or deferred to <owner>}} | |

## Human gates

{{workflow.human_gates}}
