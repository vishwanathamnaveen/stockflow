---
name: architecture-proposal
description: Structured Q&A and architecture proposal with Proposed ADRs for /propose-architecture. Use when planning topology, cloud, BFF, microservices, or client/server boundaries before sprint delivery.
---

# Architecture proposal

Optional satellite for `/propose-architecture`. Does not block the locked execute spine.

## Phases

1. **Discover** — Scan optional BRD, story pack, `config.yaml`, prior ADRs. Run [`architecture-questionnaire-template.md`](../../templates/architecture-questionnaire-template.md) for gaps; log to `artifacts/architecture/<date>-questionnaire-log.md`.
2. **Catalog** — `open-questions-cataloger` → DQ register; `nfr-checklist-builder` → cited NFR candidates only.
3. **Propose** — `architecture-proposal-writer` → proposal + ADRs + optional Mermaid topology.
4. **Validate** — Status remains **Proposed**; no Accepted ADRs; provenance on every driver.

## ADR splitting

Emit separate ADRs (status Proposed) when decisions differ on:

- Overall topology (monolith vs microservices vs modular monolith)
- BFF presence and responsibilities
- UI composition (single app vs micro-frontend)
- AuthN/Z and trust boundaries
- Data ownership and integration (sync vs events)
- Cloud/deployment model

Use [`adr-template.md`](../../templates/adr-template.md). Number sequentially under `docs/architecture/`.

## Mermaid minimum

When ≥2 deployable components exist, write `artifacts/diagrams/<date>-logical-topology.mmd` with labeled edges (protocol on arrows).

## Provenance

- Cite BRD FR/NFR, story pack, or questionnaire answers.
- Uncited choice → `ASSUMPTION-<id>` in proposal and ADR Context.
- Do not invent compliance scope or cloud account details.

## Downstream

Accepted proposal (human review) may inform `/plan-sprint`, story pack bindings, and (not in this kit). Not required for `/implement-api` or `/implement-ui`.
