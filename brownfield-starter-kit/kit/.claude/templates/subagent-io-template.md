# Subagent I/O Contract

| Field | Value |
|-------|-------|
| Subagent | |
| Parent | |
| Task | |
| Confidence | high / medium / low |

## Purpose
Single sentence: bounded task.

## Inputs
- (field: type, description)

## Outputs
- Paths:
- Unresolved assumptions:

## Failure modes
Incomplete input → return partial result with explicit gaps. Do not invent.

## Quality gate
Criteria the parent uses to accept or reject.

## Ask-backs
Questions for parent if unclear: register Open DQ. Do not invent. Do not STOP the parent except human gates.

## Audit
Parent records subagent IO in the parent audit. Optional own note only if the subagent persists files.
