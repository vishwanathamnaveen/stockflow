# ADR-{{NNN}} — {{SHORT_TITLE}}

> Architecture Decision Record. Supersedes ADR-___ when applicable. Link to stories/FR/BR when the decision traces to requirements.

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-{{NNN}} |
| **Status** | Proposed / Accepted / Deprecated / Superseded |
| **Date** | {{YYYY-MM-DD}} |
| **Deciders** | {{names or roles}} |
| **Consulted** | {{names or roles}} |
| **Command / trigger** | {{/plan-sprint, design review, etc.}} |
| **Supersedes** | ADR-___ or N/A |
| **Superseded by** | ADR-___ or N/A |

## Context

- **Problem statement:** What force or constraint requires a decision?
- **Business / technical drivers:** (cite FR/BR/NFR or ADR drivers)
- **Current state:** What exists today?
- **Constraints:** Security, compliance, timeline, team skill, existing stack
- **Assumptions:** Register `ASSUMPTION-<id>` if uncited

## Decision

- **Chosen option:** {{clear statement}}
- **Alternatives considered:**

| Option | Pros | Cons | Rejected because |
|--------|------|------|------------------|
| A | | | |
| B | | | |

- **Rationale:** Why this option wins (evidence-based)

## Consequences

### Positive

-

### Negative / trade-offs

-

### Neutral

-

## Implementation notes

| Area | Impact | Owner | Target |
|------|--------|-------|--------|
| API / contracts | | | |
| UI | | | |
| Data / migrations | | | |
| Infra / CI | | | |
| Tests | | | |
| Documentation | | | |

## Compliance and security

- **AuthN/Z impact:**
- **Data classification impact:**
- **Audit logging impact:**

## Validation

| Check | Result | Evidence |
|-------|--------|----------|
| Aligns with BRD/NFR | | |
| Reviewed by architect/SME | | |
| Rollback path documented | | |

## References

| Ref | Locator |
|-----|---------|
| BRD / story | |
| Related ADR | |
| Spike / POC | |

**Output path:** `docs/architecture/adr-{{NNN}}-{{slug}}.md` or append row to harness `decisions.md` when session-locked only.
