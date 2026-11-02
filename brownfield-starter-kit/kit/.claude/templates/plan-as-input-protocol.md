# Plan-as-input protocol

Slash commands resolve runtime inputs from **sprint plans**, **BRD**, and **prior artifacts** before registering remaining gaps.

## Plan types

| Type | Path pattern | Used by |
|------|--------------|---------|
| Sprint backlog | `artifacts/sprints/<id>-plan.md` | `/implement-api`, `/implement-ui`, expand/quality |
| BRD | `docs/requirements/brd.md` (or path in config) | `/plan-sprint`, `/generate-brd` |
| Mockup manifest | `artifacts/design/<date>-ui-mockup-manifest.md` | `/implement-ui` after `/generate-ui-design` |

## Invoker minimal prompts

```
/plan-sprint
@brd: docs/requirements/brd.md
```

```
/implement-api
@sprint_plan: artifacts/sprints/sprint1-plan.md
```

Optional: `plan_step: <n>` — otherwise first `pending` or `in_progress` row matching the command.

## Resolve-before-ask (mandatory)

When `@sprint_plan`, `@brd`, or `@mockup_path` is supplied:

1. Load plan, BRD, `docs/sprint<N>/manifest.json`, execution logs, upstream artifact paths.
2. Register Open DQ when gap register has **Open** critical items or a required binding is still `TBD`. Do not invent.
3. Never re-ask values present in workspace bindings, manifest, or execution log.
4. Skip Clarification Protocol items answerable from resolved inputs. Do not STOP except human gates.
5. After Definition of Done, update plan execution flow, execution log, and manifest.

## Command execution flow rows (command spine)

Sprint plans MUST list execute commands in this order:

`/implement-api` → `/implement-ui` → `/expand-test-coverage` → `/run-tests` → `/run-eval` → `/review-changes` → `/application-summary`

Intake/plan satellites (no harness row): `/generate-brd`, `/propose-architecture`, `/plan-sprint`, `/generate-ui-design`.
