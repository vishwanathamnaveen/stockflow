# Business Rule — {{BR_ID}}

> Single rule catalog entry. Do not invent semantics — cite source or register `ASSUMPTION-<id>` / `DQ-xxx`.

| Field | Value |
|-------|-------|
| **Rule ID** | {{BR-xxx}} |
| **Title** | {{short name}} |
| **Status** | Draft / Accepted / Disputed / Deprecated |
| **Priority** | P0 / P1 / P2 |
| **Domain** | {{bounded context}} |

## Statement

{{Precise, testable business rule in one paragraph.}}

## Provenance

| Field | Value |
|-------|-------|
| **source_path** | {{file or transcript}} |
| **source_locator** | {{section, line, timestamp}} |
| **confidence** | explicit / derived / assumption |
| **Extracted by** | requirements-agent / reverse-engineering-agent / SME |

## Triggers and scope

- **When applies:**
- **When does NOT apply:**
- **Actors:**

## Implementation hints (non-normative)

| Layer | Expected behavior | Owner agent |
|-------|-------------------|-------------|
| API | | backend-agent |
| UI | | frontend-agent |
| Data | | data-agent |

## Acceptance / test linkage

| AC ID | Test case ID | Type (+/-) |
|-------|--------------|------------|
| | TC- | |

## Related rules

| ID | Relationship |
|----|--------------|
| FR- | parent requirement |
| BR- | conflicts / depends |

## Open questions

| DQ ID | Question | Owner | Blocking |
|-------|----------|-------|----------|
| | | | |

**Output path:** `docs/reverse/business-rules/{{BR_ID}}.md` or row in BRD section 6
