# Code Generation — Do's and Don'ts

> Applies to backend-agent, frontend-agent, change-agent, and all implement commands. Enterprise-grade output only.

| Field | Value |
|-------|-------|
| **Applies to** | `/implement-api`, `/implement-ui`, (not in this kit) |
| **Enforced by** | scope.yaml, hooks, quality gates, code-review-agent |

## Do

| # | Rule | Evidence expected |
|---|------|-------------------|
| 1 | Match approved plan or cited SP/AC | audit cites plan path |
| 2 | Reuse existing controllers, services, components, hooks | no parallel duplicate types |
| 3 | Cite provenance for business behavior (rule 22) | behavior_id table in audit |
| 4 | Write tests for changed logic | test-results artifact |
| 5 | Follow agent-owned JUnit and Playwright patterns per stack-conventions.md | compile + tests pass |
| 11 | Persist template vars; run `docs/architecture/stack-conventions.md` on Java | `artifacts/templates/<resource>-vars.yaml` |
| 6 | Centralized error envelope and validation at boundaries | api-contract-template |
| 7 | Forward-only migrations | new Flyway version file |
| 8 | Write audit + update harness on phase change | artifacts/audit |
| 9 | Honor `.claude/scope.yaml` write allowlists | |
| 10 | Register Open DQ when sources silent — do not invent | DQ-xxx in audit |

## Don't

| # | Rule | Consequence if violated |
|---|------|-------------------------|
| 1 | Invent FR/BR, UI copy, API fields, error semantics | Blocked from Ready |
| 2 | Skip human gates (BRD Accepted, plan Approved, test-package Approved) | orchestrator refuse |
| 3 | Commit or log secrets, tokens, PII/PHI | security finding |
| 4 | Skip tests because change "looks small" | review block |
| 5 | Disable JaCoCo or lower coverage floors | quality-agent refuse |
| 6 | Edit applied migrations | data-agent violation |
| 7 | Add public generate or wire commands outside the locked 12-command kit catalog | catalog-lock eval fail |
| 8 | Script or run tests before `test-cases-br-coverage.md` PASS | test-agent refuse |
| 9 | Self-approve BRD or sprint plan | self-approve-forbidden eval |
| 10 | Paper over API bugs in UI | frontend-agent Must NOT |
| 11 | Skip stack-conventions layering on Java | quality/review Block |

## Ambiguity handling

- Stop on `# AMBIGUITY` in templates — do not guess structure.
- Agent-owned Java only in hybrid_policy slots; agent-owned tests cite `docs/test-cases.md` IDs.
- Max 3 loop iterations; escalate with owners after iteration 3.

**Reference:** `22-behavior-provenance-and-anti-invention.mdc`, `07-testing-and-quality.mdc`
