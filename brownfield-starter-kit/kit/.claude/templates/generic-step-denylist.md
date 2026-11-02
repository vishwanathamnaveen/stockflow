# Generic step denylist

Fail any TC whose **Steps** or **Expected Result** contain these phrases (substring match, case-insensitive). Shared by `automation-companion-author` / `test-case-generator` (must not emit) and `tc-step-quality-validator` (must fail).

| Phrase | Why it fails |
|--------|----------------|
| `Execute the workflow step matching the BR statement` | Placeholder, not executable |
| `Trigger the negative path described in the BR statement` | Placeholder, not executable |
| `Enter data that violates the BR constraint (see checklist statement)` | Generic constraint — no BR-specific invalid data |
| `Validation error is returned (or domain-specific code per BR)` | Error-code laundry list instead of the BR’s actual code |
| `Verify API/UI response matches legacy intent` | Sole verification with no observable assertion |
| `Verify {rule_name}` as the **Summary** (or `Verify ` + checklist rule name only) | Summary is not a user-visible outcome |
| `Reject {rule_name}` as the **Summary** with no failure-mode detail | Same as above for negatives |

Also fail when:

- A Constraint **negative** lists a slash-separated code set instead of the one code owned by that BR.
- Expected results name no observable UI text, HTTP status, field, or error code, **and** the TC is not Blocked.
- Steps have fewer than **2** items with a concrete UI route, named action (button / submit), or API path.

Allow a denylist phrase only if the **same TC** also contains BR-specific data that makes the phrase unnecessary — in practice, rewrite the step; do not keep the placeholder.
