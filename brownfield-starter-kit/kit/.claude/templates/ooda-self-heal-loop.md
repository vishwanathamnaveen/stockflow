# Observe → Orient → Decide → Act (self-heal)

Use **only** for `playwright-self-healer` on `/run-tests` Phase 5. This is **not** a factory-wide loop and does **not** replace Plan → Act → Validate → Refine (build/quality) or Plan → Act → Observe → Reflect (intake/reverse).

`e2e-defect-analyzer` stays a **single pass** over results. Do not put OODA on frontend-agent, backend-agent, or `/implement-ui`.

Max **3** is a **ceiling** on **suggestion quality** (rewrite the heal artifact when evidence is missing or weak). Max 3 is not a quota and is **not** a license to apply diffs.

## Observe

Load failure logs, Playwright error, trace, DOM snapshot, and the current page object under `{modules.ui}/e2e/pages/`. Optional: scan-clean Figma extract. Register Open DQ if traces are missing. Do not invent selectors.

| Input | Required |
|-------|----------|
| Playwright error (locator / strict-mode / timeout-on-selector) | Yes for a heal candidate |
| Trace or DOM snapshot | Yes — else Decide = `refuse` |
| Current POM / spec locator | Yes |
| Figma extract | Optional (must be intake-scan clean) |

## Orient

Classify the failure. First match wins.

| Class | Action |
|-------|--------|
| Locator / strict-mode / timeout-on-selector | Continue to Decide |
| Assertion, API contract, HTTP 4xx/5xx, environment down | **Stop.** Route to `e2e-defect-analyzer` only. Not a heal candidate |
| No locator failures | Decide = `N/A`. Do not invent heals |

Prefer suggested replacements: `getByRole`, `getByTestId`. CSS/XPath only when role/test-id evidence is absent — record that in the artifact. Confidence `high` only when the suggested locator appears in trace/DOM (or cited Figma). `medium` / `low` when partial. Never invent a selector with no evidence.

## Decide

| Decision | When |
|----------|------|
| `suggest` | Locator failure + evidence for a replacement |
| `N/A` | No locator failures |
| `refuse` | Missing traces/POM, or evidence does not support a selector |

Never Decide = auto-merge. Never treat assertion/API failures as heals.

## Act

Write `artifacts/issues/<date>-locator-heal.md` using `self-heal-suggestion-template.md`. Record Observe / Orient / Decide / Act in that file. **Human proceed remains pending.**

Leave product files (POM, specs) **unchanged** unless a human explicitly asks to apply the diff (`apply locator heal`). Do not auto-commit, auto-merge, or silently edit.

After a human apply, the next Observe is a **new** `/run-tests` run — do not inner-loop into apply.

## Exit

- Iteration 1 Decide is `suggest` with evidence, or `N/A` / `refuse` with rationale → **stop**. Do not start iteration 2 or 3.
- Suggestion quality findings (no evidence, wrong class, invented selector) → rewrite the artifact only (count includes the first pass; max 3).
- Still unmet after iteration 3 → escalate with Open DQ; still do not apply.

Record `iteration` in the heal artifact (use `1` when the first Decide was clean).

## Human gate

Applying a locator heal is a **human** gate (same class as test-package Approved and test-package Approved). Agents Must NOT self-apply.

**Output path:** `artifacts/issues/<YYYY-MM-DD>-locator-heal.md`
