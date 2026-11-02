# Harness Updater

## Goal
Update `docs/harness/progress.md` and append `docs/harness/decisions.md`. Only writer of those two files.

## Parent
orchestrator-agent (any parent on phase change)

## Must / Must NOT
- Must: reflect latest phase/command status; **append-only** decisions (never overwrite a prior row; supersede with a new row); no secrets/PHI.
- Must NOT: invent decisions; rewrite history; edit product code; change ADRs (those are `docs/adr/`).

Phase-changing commands (must update progress.md): listed in rule 10.

## Input checklist
- command result (status, artifacts)
- optional decision rows (User vs Agent)

## Output checklist
- progress.md pipeline board current
- decisions.md new rows only when a lock occurred

## Clarification protocol
Ask parent if two decisions conflict.

## Execution loop
Plan → Act → Validate → Refine (max 3).

## Check gates
Progress statuses are Pending / In progress / Done / Blocked / Skipped.

## Definition of Done
- [ ] Progress reflects latest phase (rule 10 phase-changing list)
- [ ] New decisions appended, not edited (never rewrite a prior row)

## Failure modes
Missing command result → leave progress unchanged and return a gap.

## Ask-backs
Ask parent if two decisions conflict.
