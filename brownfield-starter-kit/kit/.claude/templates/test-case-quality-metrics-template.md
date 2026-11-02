# Test-case quality metrics

Required section in every `/expand-test-coverage` audit **companion-quality** subsection. Silence on quality is a **FAIL** (same principle as eval-agent completeness ledger).

Thresholds from `config.yaml` → `test_cases.*` when present.

## Quality metrics

| Metric | Result | Gate |
|--------|--------|------|
| Generic-step TCs | {{n}}/{{total}} | **0** allowed (`generic_step_threshold`) |
| Misclassified negatives | {{n}} (list rule_ids) | **0** allowed |
| Missing gate negatives | {{n}} (list rule_ids) | **0** unless documented N/A |
| Incomplete BR statements inherited | {{n}} (list rule_id + DQ) | Flag; do not invent |
| Index ↔ body mismatches | {{n}} | **0** allowed |
| Blocked TCs with executable happy path | {{n}} | **0** allowed |
| Constraint negatives missing exact error code | {{n}} | **0** allowed |
| BR-specific step rate | {{pct}}% | ≥ `br_specific_step_target` when configured |

**BR-specific step:** a TC whose steps cite a concrete route/API, named action, and BR-owned data or error code — not a denylist phrase.

## Classification summary

| Classification | BR count | Positive TCs | Negative TCs |
|----------------|----------|--------------|--------------|
| constraint | | | |
| condition-gate | | | |
| condition-behavioral | | | |
| guideline / purpose / entry-criteria | | | |
| blocked | | | |

## Verdict

`PASS` only if every gate row meets its threshold. Structural BR mapping without this table is a false pass.
