# Self-heal suggestion — {{date}}

Produced by `playwright-self-healer`. Loop: Observe → Orient → Decide → Act (`ooda-self-heal-loop.md`). **Do not merge without human proceed.**

| Field | Value |
|-------|-------|
| Date | {{YYYY-MM-DD}} |
| Iteration | {{n}} of 3 |
| Scope | |
| Spec / POM | |
| Failed locator | (role/test-id/css as in error — no secrets) |
| Suggested locator | |
| Confidence | high \| medium \| low |
| Evidence | trace \| DOM snapshot \| Figma node |
| OODA Decide | suggest \| N/A \| refuse |
| Human proceed | pending |

## OODA record

| Phase | Notes |
|-------|-------|
| Observe | error / trace / DOM / POM loaded (or Open DQ) |
| Orient | locator class vs routed to e2e-defect-analyzer |
| Decide | suggest \| N/A \| refuse — never auto-merge |
| Act | artifact written; product files unchanged |

## Diff (suggestion only)

```diff
- {{old}}
+ {{new}}
```

**Output path:** `artifacts/issues/<YYYY-MM-DD>-locator-heal.md`
