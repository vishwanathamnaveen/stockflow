# /propose-architecture

## Objective
Structured **tech-stack** Q&A (with recommendations) → high-level **architecture proposal** + **Proposed** ADRs. Focused variant: no cloud/compliance questionnaire sections. **documentation-agent** mode `architecture`. Optional satellite — **not** in the locked execute spine; does **not** block `/plan-sprint` or `/implement-*`.

## When to use
- Greenfield before `/plan-sprint` or `/generate-brd`
- Major stack, cloud, or topology change
- Optional input before (not in this kit)
- When BFF, microservices, micro-frontend, or client/server boundaries need explicit documentation for downstream agents

## Runtime Inputs

### Required
- None (standalone). With zero inputs, run `tech-stack-questionnaire-template.md`.

### Optional
- `brd_path` (Draft or Accepted BRD)
- `@story_artifact` (techno-functional pack)
- Prior ADRs under `docs/architecture/`
- `cloud_target` (azure / aws / gcp / on-prem / hybrid)
- `stack_preference` (e.g. java+next, python+next)
- Compliance tags (e.g. SOC2, PCI — cite; do not assume HIPAA)
- Existing repo layout or `.claude/config.yaml` when present

## Plan-as-input mode
When `governed_plan`, `sprint_governed_plan`, or `@story_artifact` is supplied, load `.claude/skills/plan-as-input/SKILL.md` and apply `.claude/templates/plan-as-input-protocol.md` before Phase 1 Q&A. Cite resolved bindings; do not re-ask.

## Use Agents
orchestrator-agent → documentation-agent (mode `architecture`)

## Delegate to Subagents
open-questions-cataloger → tech-stack-advisor → architecture-proposal-writer

## Enforce Rules
00, 08, 09, 10, 22

## Use Templates
`tech-stack-questionnaire-template.md`, `architecture-proposal-template.md`, `adr-template.md`, `audit-trail-template.md`, `docs/architecture/stack-conventions.md`

## Use Skills
`.claude/skills/architecture-proposal/SKILL.md`

## Required Output
- `docs/architecture/<YYYY-MM-DD>-architecture-proposal.md` (status **Proposed — Pending Architecture Review**)
- `docs/architecture/adr-<NNN>-<slug>.md` (one per major decision; status **Proposed** only)
- `artifacts/architecture/<YYYY-MM-DD>-questionnaire-log.md`
- `artifacts/diagrams/<YYYY-MM-DD>-logical-topology.mmd` (when topology is described)
- `artifacts/audit/<YYYY-MM-DD>-propose-architecture-<task>.md`

## Command-Specific Hardening
- **Q&A allowed:** Ask when stack preference or module layout is unknown. Always present **Recommended** default (Java+Next) before waiting for override.
- Must NOT emit DDL, OpenAPI operation fields, or product source code.
- Must NOT mark ADRs or the proposal **Accepted** — human architecture review only.
- Must NOT append to `docs/harness/decisions.md` or call harness-updater (not phase-changing).
- Uncited topology or NFR choices → `ASSUMPTION-<id>` or Open DQ with owner ([rule 22](../rules/22-behavior-provenance-and-anti-invention.mdc)).
- Recommend future `config.yaml` binding shapes as proposals only; label assumptions when the repo is silent.
- Orchestrator and other commands **must not** refuse implement or plan gates when architecture is still Proposed.

## Execution Policy
Plan → Act → Observe → Reflect (max 3 ceiling). Iteration 1 Observe pass → stop. Reflect only from findings.

### Phases
1. **Discover** — Load optional BRD/story/config/ADRs; run questionnaire for gaps.
2. **Catalog** — `open-questions-cataloger` + `tech-stack-advisor` (recommendations + rationale).
3. **Propose** — `architecture-proposal-writer` fills proposal + ADRs + logical layers diagram (UI → API → DB).
4. **Validate** — Every major decision has an ADR or explicit DQ; no Accepted status; provenance on drivers.

## Clarification Protocol
Structured ask rounds when stack preference or module layout missing after input scan. Register remaining gaps as Open DQ. Do not invent cloud/compliance NFRs.

## Artifact Persistence
Canonical paths above. Metadata: timestamp, iteration, validation summary, source locators. No secrets in questionnaire log.

## Definition of Done
- [ ] Questionnaire log written (questions + operator answers)
- [ ] Proposal complete per `architecture-proposal-template.md` with status Proposed
- [ ] ≥1 ADR for stack choice and module layout (max 2–3 ADRs in this kit)
- [ ] All ADRs status **Proposed**; ADR index in proposal links each file
- [ ] Logical layers diagram (`artifacts/diagrams/<date>-logical-layers.mmd`)
- [ ] Suggested `config.yaml` bindings section in proposal
- [ ] Open gaps table with owners; assumptions registered
- [ ] `artifacts/audit/<date>-propose-architecture-<task>.md` written

## Next command

> ✅ `/propose-architecture` complete.
> **Next command:** `/generate-brd` or `/plan-sprint` (human chooses). Human may set ADRs to **Accepted** before planning; not required for implement spine.
