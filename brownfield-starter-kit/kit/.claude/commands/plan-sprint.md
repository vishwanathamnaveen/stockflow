# /plan-sprint

## Objective
Accepted BRD → sprint backlog tagged implement-api/ui.

Cross-artifact gap analysis is an **internal step** of this command (former internal plan step). Do not advertise a public gap command.

## Runtime Inputs

### Required
- BRD path (Accepted or waiver)
- sprint ID
- goal
- duration

### Optional
- existing UX / OpenAPI / data paths (gap-identifier; do not invent if missing)

## Plan-as-input mode
When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Clarification Protocol.

## Use Agents
orchestrator-agent → planner-agent (mode sprint)

## Delegate to Subagents
gap-identifier, sprint-planner, requirement-traceability-mapper, open-questions-cataloger

## Enforce Rules
09, 10, 11, 13, 22

## Use Templates
sprint-plan-template.md, requirement-traceability-template.md

## Use Skills
`.claude/skills/plan-as-input/SKILL.md`, `.claude/skills/planning/SKILL.md`

## Required Output
- artifacts/sprints/<id>-gap-report.md
- artifacts/sprints/<id>-plan.md

## Command-Specific Hardening
Refuse unless BRD status is **Accepted** or an explicit waiver exists in `docs/harness/decisions.md`. A BRD that remains **Draft — Pending Domain Review** cannot start `/plan-sprint`. Output status is **Proposed — Pending Approval** — agents cannot self-approve.

## Execution Policy
Loop: Plan → Act → Validate → Refine. Max 3 is a ceiling. Iteration 1 Validate pass → stop. Refine only from findings. Escalate with owners after iteration 3.

## Clarification Protocol
After resolve-before-ask, register remaining gaps as Open DQ with owner. Do not invent. Do not STOP for a clarification round except human gates (BRD Accepted, plan Approved). Still refuse when Required BRD path is absent or BRD is Draft without waiver.

## Artifact Persistence
Canonical paths above plus `artifacts/audit/<date>-<command>-<task>.md`. Metadata: timestamp, iteration, validation summary.

## Definition of Done
- [ ] Every SP maps to FR/BR
- [ ] Critical gaps owned or none
- [ ] Proposed — Pending Approval
- [ ] `artifacts/audit/<date>-plan-sprint-<task>.md` written
- [ ] Harness updated (phase-changing)

## Next command

> ✅ command complete.
> **Next command:** `/implement-api` (command spine) or /implement-api after Approval
