# /generate-brd

## Objective
Generate a structured BRD from meeting transcript(s) and supporting documents. Does **not** write user stories.

## Orchestration
| Role | Agent / Subagent |
|------|------------------|
| Orchestrator | orchestrator-agent |
| Primary | requirements-agent |
| Subagents | transcript-analyzer → supporting-doc-synthesizer → open-questions-cataloger → brd-writer |

## Runtime Inputs

### Required
- Path to transcript(s)

### Optional
- Supporting documents (or confirm transcript-only)
- Module name / bounded context
- Updating existing BRD vs new draft

## Enforce Rules
- `.claude/rules/11-intake-planning-governance.mdc`
- `.claude/rules/10-audit-trail.mdc`
- `.claude/rules/09-agent-orchestration.mdc`
- `.claude/rules/22-behavior-provenance-and-anti-invention.mdc`
- `.claude/rules/31-untrusted-intake.mdc`

## Intake safety gate
Raw transcripts and supporting docs only — not factory BRD/plan outputs. Load `.claude/skills/intake-safety/SKILL.md`. Run `python3 scripts/intake-safety-scan.py` on those paths **before** spawning requirements-agent. Exit 2 → STOP. Exit 1 → STOP until redaction or `docs/harness/decisions.md` waiver. Exit 0 → continue.

## Use Templates
`.claude/templates/transcript-intake-notes-template.md`, `brd-template.md`, `discussion-coverage-matrix-template.md`, `audit-trail-template.md`, `plan-act-observe-reflect-loop.md`

## Use Skills
`.claude/skills/intake-safety/SKILL.md`, `.claude/skills/brd-authoring/SKILL.md`

## Clarification Protocol
After resolve-before-ask, register Open DQ if missing:
1. Transcript path(s)
2. Supporting documents or transcript-only confirmation
3. Module / bounded context
4. New draft vs update of an existing BRD

Do not invent FR/BR from silence. Conflicts become DQ-xxx, not resolved requirements. Do not STOP for a clarification round except human gates. Still refuse when Required transcript path is absent. Output remains **Draft — Pending Domain Review** — never self-approve; `/plan-sprint` cannot start until Accepted or waiver.

## Execution Policy
Plan → Act → Observe → Reflect. Max 3. Then escalate with open DQs.

## Definition of Done
- [ ] Intake-safety scan exit 0, or exit 1 with recorded human redaction/waiver
- [ ] Intake notes with source traceability
- [ ] Draft BRD sections 1–16 (N/A needs a reason)
- [ ] §13 discussion coverage matrix complete
- [ ] §14 open questions with owners and Blocking flags
- [ ] Status: **Draft — Pending Domain Review**
- [ ] `artifacts/audit/<date>-generate-brd-<task>.md` written
- [ ] Harness updated (phase-changing)
- [ ] Stop before `/plan-sprint`

## Outputs
- `artifacts/intake/<date>-intake-notes.md`
- `artifacts/brd/<module>-BRD-draft.md`
- `artifacts/audit/<date>-generate-brd-<task>.md`

## Next command

> ✅ `/generate-brd` complete.
> **Next command:** `/plan-sprint` — **after** domain review. Do not run it while status is Draft.

| Condition | Next command |
|-----------|--------------|
| BRD needs domain review (default) | Wait — review the draft, then `/plan-sprint` |
| BRD already Accepted | `/plan-sprint` |
