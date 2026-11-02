---
name: api-contract-first
description: Contract-first API design and OpenAPI↔DTO sync on /implement-api. Live verify against running stack before E2E sign-off.
---

# API contract-first

## Gates (api-agent)

| Gate | When | Output |
|------|------|--------|
| 1 Design | New/changed endpoints | OpenAPI at `modules.openapi` |
| 2 Sync/verify | Every `/implement-api` | DTOs aligned; verify recorded in audit |

Do **not** skip gate 2 verify on implement runs.

## Implement flow

1. Load approved sprint plan + OpenAPI slice.
2. data-agent (ddl) when persistence changes — skill: `migration`.
3. api-agent gate 2 verify → update OpenAPI only when shape changes.
4. backend-agent + spring-module-generator per `docs/architecture/stack-conventions.md`.
5. validation-chain-generator when cited BR validation rules change — skill: `validation-chain`.
6. Slice tests + br-coverage PASS (skill: `br-coverage`).

## Live verify (before human handoff)

With stack up (`scripts/verify-stack-health.sh`):

- api-test-runner probes positive + mandatory negative cases from `docs/test-cases.md`.
- Log results in `artifacts/test-results-<date>.md`.
- Contract mismatch → **api-agent** + **backend-agent** fix; do not paper over in UI.

## Must NOT

- Invent fields, status codes, or error semantics without BRD/story citation.
- Change OpenAPI silently during review or eval fix without audit note.

## Subagents

`api-contract-designer`, `api-test-runner`, `validation-chain-generator`
