---
name: brd-authoring
description: Author a structured BRD from transcripts and supporting docs without inventing requirements. Use for /generate-brd.
---

# BRD Authoring

## Workflow

1. **Intake-safety scan** — `python3 scripts/intake-safety-scan.py` on transcripts/supporting docs; STOP on exit 2; redact/waive on exit 1.
2. **Intake first** — transcript-analyzer + supporting-doc-synthesizer before writing prose.
3. **Assign IDs** — FR (functional), BR (business rule), NFR, INT, DQ, R only from cited facts.
4. **Write sections 1–16** — do not skip; N/A needs a reason.
5. **§13 coverage matrix** — every major transcript topic → BRD section.
6. **§14 open questions** — unresolved conflicts; mark Blocking explicitly.
7. **§15 acceptance criteria** — testable, module-level.
8. **§16 test strategy** — unit / integration / E2E mapping.

## Traceability

- Each FR row: Priority (Must/Should), Source (transcript date, doc name, legacy BR-xxx).
- Mermaid for user journeys in §6 when flows are discussed.
- `[INFERRED]` claims require a DQ.

## Status header

| Status | Meaning |
|--------|---------|
| Draft — Pending Domain Review | After `/generate-brd` — needs domain review |
| Accepted | Human approved — safe for `/plan-sprint` |
| Superseded | Replaced by a newer version |

## Output path

`artifacts/brd/<module>-BRD-draft.md` until accepted; promote only on user direction.

## Do not

- Approve the BRD.
- Close DQ-xxx without a cited resolution source.
- Start `/plan-sprint` from this skill.
- Copy a legacy BRD verbatim without mapping to the new module.
