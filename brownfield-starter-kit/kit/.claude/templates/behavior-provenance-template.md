# Behavior Provenance Record

> Rule 22: every non-trivial behavior needs behavior_id, statement, source, confidence. Uncited behavior blocked from Ready.

| Field | Value |
|-------|-------|
| **Artifact** | {{BRD, story, API note, code PR}} |
| **Date** | {{YYYY-MM-DD}} |
| **Author agent** | {{name}} |

## Records

| behavior_id | statement | source_path | source_locator | confidence | status |
|-------------|-----------|-------------|----------------|------------|--------|
| BEH-001 | | | | explicit/derived/assumption | ready/blocked |

## Assumptions pending approval

| assumption_id | statement | owner | blocking |
|---------------|-----------|-------|----------|
| ASSUMPTION-001 | | | yes/no |

## Conflicts

| ID | behavior_a | behavior_b | precedence applied | resolution |
|----|------------|------------|-------------------|------------|
| BLOCKED_CONFLICT- | | | story > UX > API > code | |

## Precedence reminder

Approved story/BRD → approved UX → approved API contract → existing implementation.

**Output path:** Section in audit or `docs/quality/behavior-provenance-{{date}}.md`
