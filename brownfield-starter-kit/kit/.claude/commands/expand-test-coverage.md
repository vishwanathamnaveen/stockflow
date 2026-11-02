# /expand-test-coverage

## Invocation

`/expand-test-coverage` — close remaining FR/BR test-design gaps for the current slice (sprint item, story pack, or bounded context).

Optional: `/expand-test-coverage --stop-after=design` — case bodies + matrix + quality validators only; skip coverage gate and approval package.

## Objective

Factory **design** entry for intake, **case bodies**, **traceability matrix**, completeness, and the BR coverage gate. Stops at **Pending Approval**. Does **not** generate a manual UAT catalog, executable scripts, run suites, or eval.

## Use Agents

- orchestrator-agent
- quality-agent
- test-agent (generate mode — design only)

## Delegate to Subagents

- test-intake-normalizer (when untrusted inputs present)
- automation-companion-author (Phase 1; or test-case-generator with companion-quality DoD)
- tc-traceability-mapper (Phase 1b)
- tc-completeness-validator, tc-step-quality-validator (case bodies)
- bdd-scenario-expander (when Gherkin expansion is in scope)
- br-coverage-validator (`pre-script`)
- audit-trail-writer

Do **not** write `docs/test/manual/**`. Do **not** invoke eval-agent or `/close-eval-gaps`.

## Enforce Rules

00, 07, 09, 10, 11, 17, 22, 23 (test-generation). Untrusted intake: rule 31.

## Use Templates

`test-cases-template.md`, `test-matrix-template.md`, `test-cases-br-coverage-template.md`, `test-package-review-template.md`, `br-tc-taxonomy.md`, `generic-step-denylist.md`, `test-case-quality-metrics-template.md`, `intake-manifest.schema.md`, `bdd-test-case-template.md`, `audit-trail-template.md`, `plan-act-validate-refine-loop.md`

## Use Skills

`.claude/skills/br-coverage/SKILL.md`, `.claude/skills/quality/SKILL.md`

## Runtime Inputs

### Required

- Accepted BRD or story pack (`evals.rule_source`) — used later by `/run-eval`; required so design cites FR/BR

### Optional

- Prior implement-api/ui audits (optional for `--stop-after=design`)
- Untrusted intake (Figma extracts, Excel, CSV)

## Command-Specific Hardening

**Intake:** Untrusted inputs go through `test-intake-normalizer` and `python3 scripts/intake-safety-scan.py`. Injection (exit 2) blocks. PII (exit 1) requires human redaction. Trusted artifacts (BRD, stories, OpenAPI, checklists) are **not** scanned.

**Phase 1–1c:** Always write case bodies (full steps/expected; not matrix-only rows) and matrix. Classify BR Type **before** authoring negatives (`.claude/templates/br-tc-taxonomy.md`). Heuristic bulk scripts are forbidden.

**Phases 2–2b:** Coverage gate then Pending Approval. FAIL → expand cases; **no** `/run-tests`. Agents **Must NOT** set package Approval to Approved.

**Out of scope:** Manual UAT catalog generation/refresh; JUnit/Vitest/Playwright script generation; suite execution; eval-agent; `/close-eval-gaps`. Those belong to `/run-tests` and `/run-eval`.

**ASSUMPTION-PCC-002:** implement-api/implement-ui are **not** blocked for missing expand-gate PASS. Slice tests remain on implement-*.

## Execution Policy

Plan → Act → Validate → Refine (max 3 ceiling). Iteration 1 Validate pass → stop. Refine only from findings. Escalate with owners after iteration 3.

## Execution flow

| Phase | Role | Artifact |
|-------|------|----------|
| **Intake** (when untrusted inputs present) | test-intake-normalizer | `artifacts/test-intake/<date>-manifest.json` |
| **1 Cases** | quality-agent → test-agent + automation-companion-author | `docs/test-cases.md` |
| **1b Matrix** | tc-traceability-mapper | `docs/test-matrix.md` |
| **1c Quality** | tc-completeness-validator + tc-step-quality-validator | case bodies |
| 2 Coverage gate | quality-agent → br-coverage-validator (`pre-script`) | `docs/test-cases-br-coverage.md` — only writer; FAIL → expand cases; **no `/run-tests`** |
| 2b Human package | quality-agent | `docs/quality/test-package-review.md` **Pending Approval** (PASS only) |

If `--stop-after=design`: complete after cases + matrix + quality validators; skip Phases 2–2b.

## Decision logic

- If `evals.rule_source` missing → register Open DQ; refuse.
- If untrusted intake scan exit 2 → refuse cases until the file is cleaned.
- If untrusted intake scan exit 1 → refuse until redaction or dated waiver.
- If coverage FAIL → expand cases; do not request human approval.
- If requirements unclear → **ask user**; do not invent.

## Clarification Protocol

After resolve-before-ask, register Open DQ when `evals.rule_source` is missing or untrusted intake is blocked. Do not invent FR/BR. Do not STOP for a numbered clarification round except the human approval gate (Phase 2b) and PII-redaction halt. Still refuse when Required rule_source is absent.

## Artifact persistence

- `artifacts/test-intake/<date>-manifest.json` (when intake ran)
- `docs/test-cases.md` (Phase 1)
- `docs/test-matrix.md` (Phase 1b)
- `docs/test-cases-br-coverage.md` (Phase 2)
- `docs/quality/test-package-review.md` (Phase 2b, PASS only)
- `artifacts/audit/<date>-expand-test-coverage-<task>.md` (includes Intake + companion quality metrics)

## Definition of Done

### Phases 1–1c (always; also `--stop-after=design`)

- [ ] `docs/test-cases.md` written with **full** steps + expected per case (not matrix-only)
- [ ] `docs/test-matrix.md` indexes those cases
- [ ] Every in-scope FR/BR has ≥1 case or is Blocked with owner+reason
- [ ] `execution_layer` ∈ {api, IT, uat, integration, blocked}
- [ ] `source_path` populated when Automated ≠ NONE / not Blocked
- [ ] Negatives exist for Constraint and Condition-gate BRs (or documented N/A); **no** negatives on behavioral-assertion BRs
- [ ] Zero generic step placeholders (denylist) in case steps
- [ ] Every Constraint negative cites the BR’s exact error code + field from Source
- [ ] Completeness + step-quality validators PASS on case bodies
- [ ] Quality metrics table in expand audit
- [ ] All cases cite source FR/BR; no invented behaviors
- [ ] Manual UAT catalog was **not** created or refreshed
- [ ] Catalog was **not** produced by a heuristic generator script

### Phases 2–2b (full run; N/A for `--stop-after=design`)

- [ ] Untrusted intake scanned or documented skipped (trusted-only)
- [ ] `docs/test-cases-br-coverage.md` Status **PASS** with coverage ratio (Phase 2)
- [ ] `docs/quality/test-package-review.md` exists with **Pending Approval** (agents did not self-approve)
- [ ] No silent BR skips
- [ ] Audit written; harness updated (phase-changing)
- [ ] Executable scripts, test runs, and eval were **not** performed

## Next command

**Next command (after human sets Approval = Approved):** `/run-tests`

After `--stop-after=design`: `/expand-test-coverage` Phases 2–2b when the gate/package is ready.

```
✅ /expand-test-coverage complete.
**Next command:** /run-tests (after test-package-review Approved)
```
