# Business Requirements Document — {{PROJECT}}

> Status: **Draft — Pending Domain Review** — do not run `/plan-sprint` until **Accepted** or waiver in `docs/harness/decisions.md`.

| Field | Value |
|-------|-------|
| **BRD ID** | BRD-{{slug}} |
| **Version** | {{x.y}} |
| **Date** | {{YYYY-MM-DD}} |
| **Author** | requirements-agent |
| **Status** | Draft — Pending Domain Review |
| **Sources** | {{transcript, docs — list paths}} |

---

## 1. Purpose

- **Problem statement:**
- **Business outcomes:**
- **Success metrics:**

## 2. Scope / out of scope

| In scope | Out of scope |
|----------|--------------|
| | |

## 3. Actors and systems

| Actor | Role | Systems used |
|-------|------|--------------|
| | | |

## 4. Glossary

| Term | Definition | Source |
|------|------------|--------|
| | | |

## 5. Functional requirements (FR-xxx)

| FR ID | Statement | Priority | source_path | source_locator |
|-------|-----------|----------|-------------|----------------|
| FR-001 | | P0/P1/P2 | | |

## 6. Business rules (BR-xxx)

| BR ID | Statement | Priority | source_path | source_locator |
|-------|-----------|----------|-------------|----------------|
| BR-001 | | | | |

## 7. Data

| Entity | Description | Source |
|--------|-------------|--------|
| | | |

## 8. Integrations

| System | Direction | Protocol | Notes |
|--------|-----------|----------|-------|
| | inbound/outbound | | |

## 9. UX / journeys

| Journey | Actor | Steps summary | UX source |
|---------|-------|---------------|-----------|
| | | | |

## 10. NFRs (security, audit, performance)

| NFR ID | Category | Requirement | Target | Source |
|--------|----------|-------------|--------|--------|
| NFR-001 | security | | | |

## 11. Assumptions

| ID | Assumption | Owner |
|----|------------|-------|
| ASSUMPTION- | | |

## 12. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| | | | | |

## 13. Discussion coverage matrix

See `discussion-coverage-matrix-template.md` — every transcript topic mapped.

## 14. Open questions (DQ-xxx)

| DQ ID | Question | Owner | Blocking |
|-------|----------|-------|----------|
| DQ-001 | | | yes/no |

## 15. Testable acceptance criteria

| AC ID | Criterion | Maps to FR/BR |
|-------|-----------|---------------|
| AC-001 | | FR-001 |

## 16. Traceability to sources

| Artifact | Path | Version/date |
|----------|------|--------------|
| Transcript | | |
| Legacy doc | | |

---

## Governance

- Every FR/BR needs `source_path` + `source_locator`. Inferences need DQ-ids.
- Do not mark **Accepted** without domain review.
- Conflicts: register `BLOCKED_CONFLICT` and escalate.

**Output path:** `artifacts/brd/{{date}}-{{slug}}-brd.md`

**Next command after Accepted:** `/plan-sprint`
