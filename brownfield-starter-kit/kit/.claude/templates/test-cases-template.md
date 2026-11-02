# Test cases — {{scope}}

Designed cases only. Not scripts. Cite FR/BR/AC. Do not invent steps or expected results. Full bodies required (steps + expected). Lean/matrix-only rows are FAIL.

| case_id | title | rule_ids (FR/BR) | AC | execution_layer | type (positive/negative/blocked-path) | source_path |
|---------|-------|------------------|----|-----------------|---------------------------------------|-------------|

`execution_layer` ∈ {api, IT, uat, integration, blocked}.

## TC-{{id}} — {{title}}

- **rule_ids:** FR- / BR-
- **AC:**
- **execution_layer:** api | IT | uat | integration | blocked
- **type:** positive | negative | blocked-path
- **preconditions:** (cited)
- **steps:** (cited; numbered — at least two concrete UI route, named action, or API path steps)
- **expected:** (cited)
- **source_path / locator:**

Every in-scope FR/BR must appear on at least one case. Coverage is recorded in `docs/test-cases-br-coverage.md`. Classify Type with `br-tc-taxonomy.md` before negatives. Do not generate gap scripts until coverage is **PASS** and (for `/run-tests`) the test package is **Approved**.

**Must NOT:** emit matrix-only rows without steps/expected; write or refresh `docs/test/manual/**` on default expand.
