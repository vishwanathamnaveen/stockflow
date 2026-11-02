# Architecture Proposal — {{PRODUCT_OR_CONTEXT}}

> From `/propose-architecture`. Status **Proposed — Pending Architecture Review** until a human accepts or waives in review.

| Field | Value |
|-------|-------|
| **Proposal ID** | AP-{{YYYY-MM-DD}} |
| **Date** | {{YYYY-MM-DD}} |
| **Author** | documentation-agent (mode `architecture`) |
| **Sources** | {{BRD path, story pack, questionnaire log — cite each}} |
| **Status** | Proposed — Pending Architecture Review |

## Executive summary

- **Recommended pattern:** {{e.g. modular monolith, microservices + BFF, micro-frontend shell}}
- **One-line rationale:** (cite driver or ASSUMPTION)

## Drivers

| ID | Driver | Source | Locator |
|----|--------|--------|---------|
| FR-/NFR-/operator | | | |

## Context map

| Context | Relationship | Neighbor | Integration style | Contract ref |
|---------|--------------|----------|-------------------|--------------|
| | upstream/downstream/partnership | | sync API / events / batch | OpenAPI / event schema |

## Logical topology

> Optional Mermaid: `artifacts/diagrams/{{date}}-logical-topology.mmd`

| Component | Role | Notes |
|-----------|------|-------|
| | API service / BFF / UI shell / gateway / broker | |

### Options considered

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| A | | | chosen / rejected |

## Cloud and deployment

| Concern | Choice | Source / ASSUMPTION |
|---------|--------|---------------------|
| Cloud / on-prem | | |
| Regions / DR | | |
| Environments | dev / staging / prod | |
| Compute | | |
| Identity / secrets | refs by name only | |

## Tech stack

| Layer | Technology | Maps to config binding |
|-------|------------|------------------------|
| API | | `modules.api` |
| UI | | `modules.ui` |
| Contract | | `modules.openapi` |
| Data | | |
| Messaging | | |
| Infra | | `modules.infra` |

## Client / server model

| Concern | Decision | Cite |
|---------|----------|------|
| UI rendering | SSR / CSR / hybrid | |
| API exposure | browser-direct / BFF / gateway | |
| Auth flow | | |
| Session / token handling | | |

## Integration patterns

| System | Direction | Protocol | Notes |
|--------|-----------|----------|-------|
| | inbound/outbound | REST / events / batch | BRD §8 or questionnaire |

## Security and data

| Trust boundary | Controls | Data classification |
|----------------|----------|---------------------|
| | AuthN/Z, encryption | |

## NFR targets

| NFR | Target | Verification | Source |
|-----|--------|--------------|--------|
| | | | nfr-checklist-builder |

## ADR index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | | Proposed |
| ADR-002 | | Proposed |

## Open gaps

| DQ ID | Gap | Owner | Blocking |
|-------|-----|-------|----------|
| | | | yes/no |

## Implementation bindings (for downstream)

Copy accepted sections into:

- Sprint plan workspace bindings (`sprint-plan-template.md`)
- Requirement traceability (`requirement-traceability-template.md`) when using `/plan-sprint`

## Approval

| Reviewer | Date | Status |
|----------|------|--------|
| | | Proposed — Pending Architecture Review / Accepted |

**Output path:** `docs/architecture/{{YYYY-MM-DD}}-architecture-proposal.md`
