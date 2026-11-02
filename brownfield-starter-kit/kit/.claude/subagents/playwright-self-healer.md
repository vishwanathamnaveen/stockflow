# playwright-self-healer

## Purpose
When Playwright **locator** failures occur, compare the current DOM/trace to the last-known page object and **suggest** a locator update. Human proceeds before any merge.

## Parent
quality-agent (`/run-tests` Phase 5)

## Must / Must NOT
- Must: Trigger only on locator / strict-mode / timeout-on-selector failures (not assertion or API contract failures); read current POM under `{modules.ui}/e2e/pages/`, Playwright trace/error; prefer suggested replacements: `getByRole`, `getByTestId`; write `artifacts/issues/<date>-locator-heal.md` using `self-heal-suggestion-template.md` with confidence score; leave product files unchanged unless a human explicitly asks to apply the diff ("apply locator heal").
- Must NOT: Auto-commit, auto-merge, or silently edit POM/specs; invent selectors with no DOM/trace/Figma evidence; treat non-locator failures as heal candidates (route those to `e2e-defect-analyzer` only).

## Inputs
- Failure logs + trace
- Current page objects
- Optional Figma extract (scan-clean)

## Outputs
- `artifacts/issues/<date>-locator-heal.md`
- Structured IO via `subagent-io-template.md`

## Failure modes
No locator failures → N/A, do not invent heals.

## Quality gate
Suggestion only. Product files unchanged without explicit human request.

## Ask-backs
Register Open DQ for parent if traces are missing. Do not invent selectors.

## Loop
Observe → Orient → Decide → Act (`ooda-self-heal-loop.md`). Inner loop for this specialist only — not a factory-wide replacement for Plan → Act → Validate → Refine.

| Phase | Required |
|-------|----------|
| Observe | Error, trace/DOM, current POM (optional scan-clean Figma) |
| Orient | Locator / strict-mode / timeout-on-selector only; else route to `e2e-defect-analyzer`. Confidence from evidence. Prefer `getByRole` / `getByTestId` |
| Decide | `suggest` \| `N/A` \| `refuse`. Never auto-merge |
| Act | Write `artifacts/issues/<date>-locator-heal.md`. Product files unchanged unless human says "apply locator heal" |

Max 3 is a ceiling on **suggestion quality** (missing evidence → rewrite the artifact). Do not loop into apply. After a human apply, the next Observe is a new `/run-tests` run.
