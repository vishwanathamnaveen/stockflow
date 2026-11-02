# BDD Test Case — {{CASE_ID}}

> Expanded from Gherkin for `/expand-test-coverage`. Maps to AC; feeds test-cases.md structure.

| Field | Value |
|-------|-------|
| **Case ID** | TC-{{id}} |
| **Feature file** | {{path}} |
| **Scenario name** | {{name}} |
| **AC refs** | {{AC-ids}} |
| **rule_ids** | {{FR-/BR-}} |

## Gherkin source

```gherkin
(paste scenario)
```

## Structured case (for test-cases.md)

- **title:**
- **layer:** unit | IT | e2e
- **type:** positive | negative
- **preconditions:** (cited)
- **steps:** (numbered, cited)
- **expected:** (cited)
- **source_path / locator:**

## Automation mapping

| Step | UI action / API call | Page object / fixture |
|------|----------------------|------------------------|
| 1 | | |

## Tags

@AC- @positive|@negative @layer-e2e

**Output path:** Row in `docs/test-cases.md` + `docs/test-matrix.md`
