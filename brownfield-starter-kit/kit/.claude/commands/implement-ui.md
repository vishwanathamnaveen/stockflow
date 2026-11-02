# /implement-ui

## Objective
UI slice from mockup, Figma sketch, or UX spec: components → **FE↔BE wiring (required gate)** → UI/e2e tests. Presentational and adapter work are one command; wiring is not optional and is not a public `/wire-*` command.

## When to use
After `/implement-api` for the same sprint item, or when the item is UI-only with a stable contract.

## Orchestration
| Phase | Role | Agent / Subagent |
|-------|------|------------------|
| 1 Layout | If mockup/sketch | mockup-to-component |
| 2 Components | Primary | frontend-agent + next-component-generator |
| 3 Wiring | Required gate | frontend-agent (wiring check gate) |
| 4a Cases | Design | test-case-generator + e2e-scenario-writer (if journey changed) → `docs/test-cases.md` + matrix |
| 4b Coverage gate | Required | quality-agent → br-coverage-validator (`pre-script`). Only writer of `docs/test-cases-br-coverage.md`. FAIL → expand cases; do not run |
| 4c Execute | After PASS | ui-test-runner |

A flowchart/whiteboard is **not** a page — run `/generate-ui-design` with a reference URL or cite an approved UX spec; do not invent screens from sketches alone.

## Execution order
```
Plan
 → Act
 → mockup-to-component or UX spec
 → next-component-generator
 → frontend-agent wiring gate
 → test-case-generator [+ e2e-scenario-writer if journey changed]
 → test-cases-br-coverage gate (PASS required)
 → ui-test-runner
 → Validate → Refine (max 3)
```

## Runtime Inputs

### Required
- Approved plan or SP item

### Optional
- `mockup_path` — prefer PNG from `/generate-ui-design` (`artifacts/design/*-mockup.png` or manifest JSON)
- `figma_url` (node screenshot — not DS extract), `governed_plan`

## Plan-as-input mode
When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Clarification Protocol.

## Enforce Rules
00, 02, 04, 05, 07, 09, 10, 22

## Use Templates
`plan-act-validate-refine-loop.md`, `ui-spec-template.md`, `test-cases-template.md`, `test-cases-br-coverage-template.md`, `test-matrix-template.md`, `test-results-template.md`, `e2e-test-results-template.md`, `audit-trail-template.md`

## Use Skills
`.claude/skills/plan-as-input/SKILL.md`, `.claude/skills/playwright-e2e/SKILL.md`

## Clarification Protocol
After resolve-before-ask, if neither mockup (including `/generate-ui-design` output), Figma sketch, UX spec, nor story UI table is available, register an Open DQ. Do not invent copy or API fields. Do not STOP for a clarification round except human gates (plan **Approved**). Still refuse when the sprint/governed plan is not **Approved**.

## Command-Specific Hardening
- Refuse unless the sprint/governed plan is **Approved**. **Proposed — Pending Approval** is not enough. Orchestrator refuses implement-* until Approved.
- **ASSUMPTION-PCC-002:** expand coverage PASS does **not** block this command. Slice cases + BR coverage + UI tests still run here. Remaining FR/BR gap scripts belong to `/run-tests` after expand package Approved.
- Wiring is a required check gate.
- Do not write API business logic.
- Stay in frontend-agent `scope.yaml` allowlist.

## Definition of Done
- [ ] Components exist for the slice
- [ ] Wiring gate passed (typed client, ordered sequence, traceability)
- [ ] `docs/test-cases.md` + matrix include the UI slice
- [ ] `docs/test-cases-br-coverage.md` Status **PASS** before runners
- [ ] UI unit/component tests run (`npm test` or project equivalent)
- [ ] E2E if journey changed
- [ ] `artifacts/audit/<date>-implement-ui-<task>.md` written
- [ ] Harness updated (phase-changing)

## Next command

> ✅ `/implement-ui` complete.
> **Next command:** `/expand-test-coverage`
