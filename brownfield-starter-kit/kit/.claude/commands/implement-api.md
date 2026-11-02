# /implement-api

## Objective
Backend slice for one sprint item or governed-plan step: schema/DDL → OpenAPI → Spring → **tests run**. Does not write UI.

## When to use
After `/plan-sprint` (**Approved**). Manual per SP item, or as the first execute step in the command spine.

## Orchestration
| Phase | Role | Agent / Subagent |
|-------|------|------------------|
| 1 Schema | If persistence changes | data-agent (mode ddl) / schema-migration-generator |
| 2 Contract | Always | api-agent gate 1 (design) + gate 2 (OpenAPI sync/verify) |
| 3 Spring slice | Primary | backend-agent + spring-module-generator (agent-owned per `docs/architecture/stack-conventions.md`) |
| 3b Validation | If cited validation BRs change | validation-chain-generator |
| 4a Cases | Design | test-case-generator → `docs/test-cases.md` + `docs/test-matrix.md` |
| 4b Coverage gate | Required | quality-agent → br-coverage-validator (`pre-script`). Only writer of `docs/test-cases-br-coverage.md`. FAIL → expand cases; do not script |
| 4c Scripts | After PASS | spring-test-generator (agent-owned JUnit per stack-conventions) |
| 4d Execute | Run | api-test-runner |

api-agent gate 2 is not optional. Every run starts with at least a contract **verify**. Full OpenAPI edit only when endpoints/DTOs/status codes change.

## Execution order
```
Plan
 → schema-migration-generator (if tables/columns/indexes/seeds change)
 → api-agent (verify; update OpenAPI if shape changes)
 → backend-agent + spring-module-generator
 → validation-chain-generator (if cited validation BRs change)
 → test-case-generator (`docs/test-cases.md` + matrix)
 → test-cases-br-coverage gate (PASS required)
 → spring-test-generator
 → api-test-runner (tests MUST run)
 → Validate → Refine (max 3)
```

Internal generate-* steps are **not** public commands.

## Runtime Inputs

### Required
- Approved plan or SP item
- `implementation_module_root` (or resolved from governed plan)

### Optional
- `governed_plan`, `plan_step`

## Plan-as-input mode
When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Clarification Protocol.

## Enforce Rules
00, 02, 03, 05, 07, 09, 10, 14, 22, 23

## Use Templates
`backend-rest-orchestration-pattern.md`, `api-contract-template.md`, `test-cases-template.md`, `test-cases-br-coverage-template.md`, `test-matrix-template.md`, `test-results-template.md`, `feature-note-template.md`, `audit-trail-template.md`, `docs/architecture/stack-conventions.md`

## Use Skills
`.claude/skills/plan-as-input/SKILL.md`, `.claude/skills/api/SKILL.md`, `.claude/skills/jacoco-coverage/SKILL.md`, `.claude/skills/validation-chain/SKILL.md`, `.claude/skills/migration/SKILL.md`

## Clarification Protocol
After resolve-before-ask, register remaining gaps as Open DQ for bindings still TBD. Do not invent. Destructive DDL requires quoted story AC. Do not STOP for a clarification round except human gates. Still refuse when the plan is not **Approved**.

## Command-Specific Hardening
- Refuse unless the sprint/governed plan is **Approved**. **Proposed — Pending Approval** is not enough.
- **ASSUMPTION-PCC-002:** expand coverage PASS does **not** block this command. Slice cases + BR coverage + product tests still run here. Remaining FR/BR gap scripts belong to `/run-tests` after expand package Approved.
- **Agent-owned implement:** Spring/DTO generation per `docs/architecture/stack-conventions.md` (no J2 template render pipeline).
- Agent-owned Java: controller, service, repository, DTO, entity, mapper, ValidationRule when cited. Tests cite `docs/test-cases.md` IDs.
- Note conventions compliance in audit (packages, layering, OpenAPI alignment).
- Must NOT swallow frontend or change BR meaning without user confirmation.
- Stay in `scope.yaml` write allowlist for backend-agent / api-agent.

## Definition of Done
- [ ] Internal order complete
- [ ] api-agent contract verify recorded
- [ ] Flyway/Liquibase + JPA when persistence changed
- [ ] `docs/test-cases.md` + matrix written for the SP item
- [ ] `docs/test-cases-br-coverage.md` Status **PASS** before scripts
- [ ] Unit/IT agent-owned per stack-conventions; cite test case IDs
- [ ] Stack conventions compliance noted in audit
- [ ] Tests actually run; `artifacts/test-results-<date>.md` updated
- [ ] No UI files written
- [ ] `artifacts/audit/<date>-implement-api-<task>.md` written
- [ ] Harness updated (phase-changing)

## Outputs
- API module sources
- migrations (when needed)
- OpenAPI
- `artifacts/test-results-<date>.md`
- `artifacts/audit/<date>-implement-api-<task>.md`

## Next command

> ✅ `/implement-api` complete.
> **Next command:** `/implement-ui` if this item has UI; otherwise `/expand-test-coverage`.
