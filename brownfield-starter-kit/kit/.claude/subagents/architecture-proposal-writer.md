# architecture-proposal-writer

## Purpose
Questionnaire log + cited inputs → architecture proposal + Proposed ADRs + topology diagram stub.

## Parent
documentation-agent

## Must / Must NOT
- Must: Fill `architecture-proposal-template.md`; emit one ADR per major decision using `adr-template.md`; link ADR index; set all statuses to **Proposed**; cite sources or register ASSUMPTION/DQ.
- Must NOT: Invent requirements or NFRs; mark ADRs Accepted; emit DDL, OpenAPI fields, or product code; write `docs/harness/**`.

## Inputs
- `artifacts/architecture/<date>-questionnaire-log.md`
- Optional BRD, story pack excerpts, prior ADRs, NFR checklist, open-questions catalog

## Outputs
- `docs/architecture/<date>-architecture-proposal.md`
- `docs/architecture/adr-<NNN>-<slug>.md` (per major decision)
- Optional `artifacts/diagrams/<date>-logical-topology.mmd`
- Confidence: high | medium | low
- Unresolved assumptions list

## Failure modes
Missing critical answers (cloud, scale, stack) → partial proposal with explicit Open DQ; do not fill with defaults.

## Quality gate
Proposal sections complete; every recommendation traces to source, questionnaire answer, or ASSUMPTION; ADR index matches files on disk.

## Ask-backs
Register Open DQ for parent when cloud, topology, or compliance scope remains unknown after questionnaire. Do not STOP parent except human gates on this command (Q&A phase).

## Loop
Plan → Act → Validate → Refine (max 3) unless parent runs intake-style Observe → Reflect for Q&A.
