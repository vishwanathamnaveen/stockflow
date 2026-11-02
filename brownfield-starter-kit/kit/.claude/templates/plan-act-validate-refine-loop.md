# Plan → Act → Validate → Refine

Use for **build, quality, codegen**. Max **3** iterations. Max 3 is a **ceiling**, not a quota.

## Plan
Load command contract, rules, skills, templates, `config.yaml`, `scope.yaml`. Register Open DQ if required inputs are missing after resolve-before-ask. Still refuse when a human gate is unmet or a Required input is absent. Select subagents. Set acceptance threshold.

## Act
Produce enterprise-grade code/docs/tests. No workarounds. Stay inside `scope.yaml` write allowlist.

## Validate
Run named validators (tests, linters, coverage, eval cases). Score against command Definition of Done. **Never skip Validate.** Absence of a validator run is not a pass.

## Refine
**Only from findings.** Patch in place from Validate failures. Increment iteration.
If Validate is clean, do not Refine.

## Exit
- Iteration 1 Validate meets the command Definition of Done → **stop**. Do not start iteration 2 or 3.
- Findings remain → Refine, then Act again (count includes the first pass; max 3).
- Still unmet after iteration 3 → escalate with audit gaps and owners.

Record `iteration` in the audit (use `1` when the first Validate passed).

## Completion
Always tell the user **Next command** from the command file.
