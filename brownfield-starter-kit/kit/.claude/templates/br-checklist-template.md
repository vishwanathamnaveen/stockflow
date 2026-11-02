# Business Rule Checklist — {{SCOPE}}

> Pre-implementation or review checklist for BR-xxx coverage. Every row must cite a source or register DQ-xxx.

| Field | Value |
|-------|-------|
| **Scope** | {{sprint, slice, release}} |
| **BRD / story pack** | {{path}} |
| **Reviewer** | {{role}} |
| **Date** | {{YYYY-MM-DD}} |
| **Status** | In progress / Complete |

## Rule inventory

| BR ID | Statement (short) | Source path | Locator | Priority | Implementation target | Test case(s) | Status |
|-------|-------------------|-------------|---------|----------|----------------------|--------------|--------|
| BR-001 | | | | P0/P1/P2 | API / UI / both | TC- | Not started / In progress / Done / Waived |

## Validation dimensions

| Dimension | Question | Pass criteria |
|-----------|----------|---------------|
| Provenance | Is every BR cited? | source_path + locator or DQ |
| API | Is rule enforced server-side? | controller/service + OpenAPI |
| UI | Is rule reflected in UX? | component/validation + ui-spec |
| Data | Is rule enforced in DB/constraints? | migration/check constraint |
| Tests | Positive + negative cases? | test-cases.md + PASS coverage |
| Errors | Correct error semantics? | matches api-contract envelope |

## Conflicts and ambiguities

| ID | BR IDs involved | Conflict | Resolution / owner |
|----|-----------------|----------|-------------------|
| DQ- | | | |

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Domain SME | | | |
| Tech lead | | | |

**Output path:** `docs/quality/br-checklist-{{date}}-{{slug}}.md`
