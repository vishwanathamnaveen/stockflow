# tc-traceability-mapper

## Purpose
Build the FR/BR ↔ case ↔ story ↔ automated-test traceability matrix. Canonical path is `docs/test-matrix.md`.

## Parent
quality-agent (`/expand-test-coverage` Phase 1b)

## Must / Must NOT
- Must: Map every case to its source FR/BR with explicit `rule_ids` on every matrix row; TC ID column = case_id from `docs/test-cases.md`; carry `execution_layer`, `source_path` from case bodies; mark `NONE — gap for expand-test-coverage` when no automated test exists and the BR is not Blocked; mark `NONE (Blocked)` when the BR is Blocked — **not** an expand gap; emit Layer Summary.
- Must NOT: Write `*.java`, `*.ts(x)`, `evals/**`, or generator scripts; write the UAT catalog or coverage gate file; fail the run for `Automated = NONE` on non-Blocked BRs (hint, not a gate); invent story or test links not present in source artifacts; count Blocked rows as expand-test-coverage gaps.

## Inputs
- Case bodies (`docs/test-cases.md` from automation-companion-author / test-case-generator)
- `evals.rule_source` or cited FR/BR
- Traceability file (optional)

## Outputs
- `docs/test-matrix.md`
- Structured IO via `subagent-io-template.md` with confidence + assumptions

## Failure modes
Missing case bodies → refuse. Do not invent rows.

## Quality gate
Every case in `docs/test-cases.md` has a matrix row. Index is not a substitute for case bodies.

## Ask-backs
Register Open DQ for parent if unclear. Do not invent.

## Loop
Single pass; parent persists output after completeness **and** step-quality validators pass.
