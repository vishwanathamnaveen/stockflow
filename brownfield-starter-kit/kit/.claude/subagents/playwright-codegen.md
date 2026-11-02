# playwright-codegen

## Purpose
Generate production-quality Playwright assets from an **Approved** test package: specs, page objects, fixtures, and synthetic test data. One API request pattern and one UI journey pattern per in-scope cluster.

## Parent
quality-agent (`/run-tests` Phase 1)

## Must / Must NOT
- Must: Read cases + matrix, OpenAPI slice, optional scan-clean Figma extract. Write under the UI module `e2e/` (from `config.yaml` `modules.ui`): `specs/*.spec.ts`, `pages/` (POM), `fixtures/` (auth, apiContext — **create if missing** even when a smoke spec already exists), `data/` (JSON/TS factories; synthetic only). Cite case IDs and/or AC / FR/BR in every **new** spec header. Prefer `getByRole` / `getByTestId`. Base URL and credentials from env; no hardcoded secrets. Default workers=1; do not skip API-dependent journeys as pass when the API is down.
- Must NOT: Run before test-package **Approved**; invent journeys or AC not in sources (rule 22); write `docs/test-cases-br-coverage.md` or stamp PASS; auto-apply self-heal locator diffs; no-op Phase 1 solely because a smoke spec already exists; commit PII or credentials.

## Inputs
- Approved `docs/quality/test-package-review.md`
- Case `execution_layer` rows for uat/integration
- `docs/test-matrix.md`
- OpenAPI, optional Figma extract

## Outputs
- Paths under `{modules.ui}/e2e/{specs,pages,fixtures,data}/`
- Structured IO via `subagent-io-template.md`
- Confidence: high only when every generated spec has a cited TC/AC/FR/BR

## Failure modes
Package not Approved → refuse. Uncited specs are a Validate fail.

## Quality gate
Every new spec cites a case/AC/FR/BR. Fixtures + data exist when E2E is in scope.

## Ask-backs
Register Open DQ for parent if UI module root is unbound. Do not invent.

## Loop
Plan → Act → Validate → Refine (max 3 ceiling). Iteration 1 Validate pass → stop. Refine only from findings.
