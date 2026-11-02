# Agent Audit — {{COMMAND}} — {{TASK}}

> Aligns with `docs/harness/progress.md`. No secrets, credentials, or PHI/PII.

| Field | Value |
|-------|-------|
| **Date** | {{YYYY-MM-DD}} |
| **Command / Agent** | {{/command or agent}} |
| **Iteration** | {{n}} of 3 |
| **Validation** | {{summary}} |

## What
- Files created/modified

## Why
- User request / BR# / story / plan reference

## How
- Rules, templates, skills, subagents, commands run

## Validation
| Check | Result | Evidence |
|-------|--------|----------|
| Inputs complete | | |
| DoD checklist | | |
| Tests / evals | | |
| Scope allowlist | | |

## Behavior provenance
| behavior_id | statement | source | confidence |
|-------------|-----------|--------|------------|

## Open items
-

## Next command
`/{{next}}`

**Output path:** `artifacts/audit/{{date}}-{{command}}-{{task}}.md`
