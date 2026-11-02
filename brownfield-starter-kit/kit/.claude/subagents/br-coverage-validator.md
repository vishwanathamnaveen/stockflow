# br-coverage-validator

## Goal
Validate `docs/test-cases-br-coverage.md` completeness and stamp PASS/FAIL. Only this subagent writes the coverage file.

## Invoked by
quality-agent on `/expand-test-coverage` (Phase 2) and before `/run-tests` script generation.

## Must NOT
Lower gates; invent AC; stamp PASS without running validators.
