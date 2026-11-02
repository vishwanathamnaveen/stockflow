---
name: validation-chain
description: Implement ValidationRule chains and tests when cited BRs change during /implement-api.
---

# Validation chain

Invoke **validation-chain-generator** when a story or BRD cites business validation rules that need Spring `ValidationRule` implementations.

## Steps

1. Load cited BR IDs from sprint plan / BRD — no invented rules.
2. Generate rule classes + registration in service layer per `docs/architecture/stack-conventions.md`.
3. test-case-generator adds positive + mandatory negative cases per rule branch.
4. br-coverage-validator PASS before tests run.

## Quality gate

Every rule branch: at least one pass test and one fail test citing case IDs.

## Must NOT

Replace test-agent case design or skip br-coverage gate.

## Subagent

`validation-chain-generator`
