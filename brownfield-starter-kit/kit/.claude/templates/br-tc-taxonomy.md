# BR → Test-Case Taxonomy

Canonical classification for `/expand-test-coverage` case design. All agents and subagents **load this file** — do not restate a divergent rule in a local prompt.

Classify from the checklist or BRD **`Type` column first**. Do not keyword-scan statement text for `"validation"`, `"error"`, or `"gate"` unless the Type already permits a negative (see below).

## Classification table

| Source `Type` | Positive TC | Negative TC |
|---------------|-------------|-------------|
| **Constraint** | Valid input passes | Invalid input → the BR’s actual error code and field |
| **Condition** (gate: auth, closed, unauthorized, forbidden) | Authorized / open / allowed passes | Unauthorized / closed / forbidden is rejected with the sourced code |
| **Condition** (behavioral: “not invoked”, “does not run”, “intentionally not”) | Verify the behavior holds | **No negative** |
| **Guideline** / **Purpose** / **Entry Criteria** | Workflow verification | Only if the source **explicitly** describes a reject path, **or** the rule **name** contains `Validation`, `Restriction`, or `Gate` |
| **Blocked** | Placeholder documenting the block | Optional “must not invent behavior” check — not an executable happy path |

Unlisted Type values: treat as **Guideline** (positive only) and open `DQ-nnn` if a reject path is implied but not explicit.

## Negative generation denylist

Do **not** create a negative TC when any of these hold:

1. Statement (case-insensitive) matches: `not invoked`, `does not run`, `intentionally not`, `unlike other`.
2. Type is `Purpose` or `Guideline` **and** the rule name does **not** contain `Validation`, `Restriction`, or `Gate`, **and** the statement does not describe a reject/error path.
3. Type is `Condition` and the statement asserts a non-failure behavior (something that is skipped, not run, or not called).

Keyword `"validation"` inside a behavioral Condition (e.g. “location validation step is not invoked”) is **not** a Constraint.

## Gate Conditions (negative required)

A Condition is a **gate** when the statement requires a proof, authorization, open-state, or role before the workflow continues. Those BRs **must** have an unauthorized/closed/forbidden negative **or** a documented `N/A` with reason in the catalog.

## Incomplete BR statements

Flag rows whose statement is truncated or empty-parenthetical, for example:

- `must match ()`
- `values ().`
- any `()` with no inner text where a code, field, or limit is expected

Open `DQ-nnn` **before** authoring. Do not invent the missing parenthetical. Steps may still be authored when a **cited** automated test or domain-service method supplies the concrete data — record that as `Source`, not as invented BR text.

## Blocked BR TC shape

- `Automated`: `NONE (Blocked)`
- `Type`: `positive` (block documentation) — negative optional only as “must not invent”
- Steps document the block (owner, DQ id, what must not be claimed)
- Steps are **not** an executable happy path that pretends the BR is implemented
