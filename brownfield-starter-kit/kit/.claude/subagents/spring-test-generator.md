# spring-test-generator

## Purpose
Generate JUnit tests per `docs/architecture/stack-conventions.md`.

## Parent
backend-agent

## Must / Must NOT
- Must: Cite `docs/test-cases.md` case IDs in test names; cover positive and mandatory negatives.
- Must NOT: Script before `docs/test-cases-br-coverage.md` Status is **PASS**.

## Inputs
- `docs/test-cases.md` slice for the SP item
- module root from config

## Outputs
- JUnit sources (registry-style structure + agent-owned sibling classes when needed)
- Confidence: high | medium | low
- Unresolved assumptions list

## Failure modes
Incomplete input → partial result with explicit gaps.

## Quality gate
Refuse unless br-coverage-validator **PASS** for in-scope FR/BR. Tests map to case IDs. Note compliance in parent audit.

## Ask-backs
Register Open DQ for parent if unclear. Do not invent. Do not STOP the parent except human gates.

## Loop
Plan → Act → Validate → Refine (max 3).
