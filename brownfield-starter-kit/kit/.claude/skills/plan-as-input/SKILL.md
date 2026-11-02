---
name: plan-as-input
description: Resolve-before-ask when a command receives @sprint_plan, @brd, or @mockup_path — load artifacts first; register Open DQ for TBD bindings.
---

# Plan-as-input (resolve-before-ask)

Full protocol: `.claude/templates/plan-as-input-protocol.md`.

## Trigger

`@sprint_plan:`, `@brd:`, or `@mockup_path:` on `/implement-api`, `/implement-ui`, `/plan-sprint`, and other governed commands.

## Resolution order

1. Gap gate — Open **critical** items (authz / money / PII / breaking schema) → hard-stop.
2. Plan step — explicit `plan_step`, else first `pending` row for this command.
3. Workspace bindings — module roots, OpenAPI path, UI mockup manifest.
4. Upstream artifacts from execution log and `docs/sprint<N>/manifest.json`.
5. Repo introspection only when non-behavioral.
6. Remaining `TBD` → register Open DQ with owner. Do not STOP except human gates.

## After Definition of Done

Update plan execution flow, execution log, and manifest.
