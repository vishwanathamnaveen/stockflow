# tc-completeness-validator

## Purpose
Validate structural completeness: every in-scope FR/BR maps to at least one case (or is Blocked with owner+reason), required negatives exist **per taxonomy**, index matches case bodies, and layer/source_path rules hold. Silence (no case, no Block) is a finding — not a pass.

## Parent
quality-agent (`/expand-test-coverage` Phase 1c)

## Must / Must NOT
- Must: Load rule source, `docs/test-cases.md`, `docs/test-matrix.md`, and `.claude/templates/br-tc-taxonomy.md`. Check: every FR/BR has ≥1 case_id **or** is Blocked with owner; every BR the taxonomy marks **negative-required** has at least one negative case, or a note `Negative: N/A — {reason}`; BRs the taxonomy **forbids** a negative for do **not** have a failure-path negative; index rows and case bodies agree; `execution_layer` ∈ {api, IT, uat, integration, blocked}; `source_path` required when Automated ≠ NONE and not Blocked; case rows have steps + expected (matrix-only rows FAIL); every matrix row lists explicit `rule_ids`. Return structured pass/fail with a gap list.
- Must NOT: Write case bodies (that is automation-companion-author / test-case-generator); score step prose quality (that is `tc-step-quality-validator`); write product tests or evals; require a UAT catalog; waive missing cases or convert gaps to passes; invent FR/BR.

## Inputs
- `evals.rule_source` or cited FR/BR
- `docs/test-cases.md`
- `docs/test-matrix.md`
- Taxonomy template

## Outputs
- Completeness result: pass/fail
- Gap list: `[{rule_id, check, reason}]`
- Structured IO via `subagent-io-template.md`

## Failure modes
Missing cases file or rule_source → fail. Frozen UAT catalog missing is **not** a completeness fail.

## Quality gate
Pass or fail. No third “implied pass.” Parent re-delegates to automation-companion-author for gaps.

## Ask-backs
Register Open DQ for parent if rule source or case file is missing. Do not invent.

## Loop
Single pass; quality phrasing is validated separately by `tc-step-quality-validator` — both must pass.
