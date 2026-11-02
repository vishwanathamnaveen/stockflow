# Agent Contract Template

Every agent in `.claude/agents/` MUST use these sections. Tailor content; do not ship empty headings.

## Goal
One sentence: the outcome this agent is accountable for.

## Must / Must NOT
- Must: bounded job
- Must NOT: sibling agent work, self-approval, invention, secrets in audits

## Input checklist
- Required fields (type, path pattern)
- Optional fields and defaults

## Output checklist
- Artifact paths
- Confidence: high | medium | low
- Unresolved assumptions

## Clarification protocol
After resolve-before-ask, register remaining Open DQs. Do not invent. Do not STOP except human gates (BRD Accepted, plan Approved). Still refuse when a Required input is absent.

## Execution loop
Build/quality: Plan → Act → Validate → Refine (max 3, ceiling).
Intake/reverse: Plan → Act → Observe → Reflect (max 3, ceiling).
Specialist (self-heal only): `playwright-self-healer` uses Observe → Orient → Decide → Act (`ooda-self-heal-loop.md`). Not a third factory-wide loop. Mutating Act requires human proceed. `e2e-defect-analyzer` is a single pass (not OODA).
Never skip Validate/Observe. First Act is final only when Validate/Observe meets DoD; otherwise Refine/Reflect. Do not start iteration 2 or 3 when iteration 1 already passed.

## Check gates
Named validators or subagents the parent uses to accept/reject output.

## Definition of Done
Checkbox list tied to outputs. Cannot self-approve human gates.

## Audit and harness
Write `artifacts/audit/<YYYY-MM-DD>-<agent-slug>-<task>.md`.
On phase change, delegate `harness-updater` (only writer of `docs/harness/progress.md` and `docs/harness/decisions.md`).

## Human gates
What this agent must not auto-approve.

## Delegates
Subagents only. Do not perform a sibling agent's job.
