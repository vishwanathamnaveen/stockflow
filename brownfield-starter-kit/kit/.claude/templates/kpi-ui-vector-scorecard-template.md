# UI Vector Scorecard — <app> — Sprint <sprint_number>

## Metadata

| Field | Value |
|-------|-------|
| Run ID | <run_id> |
| Validation scope | sprint / overall |
| Sprint number | <sprint_number> (omit for overall-only) |
| App | <modules.ui> |
| Overall score | <overall_score> / 10 |
| Overall status | Green / Amber / Red |
| Generated (UTC) | <timestamp> |

## Scorecard (0–10)

| Vector | Score | Status | Evidence summary |
|--------|-------|--------|------------------|
| Path Traversal | <n>/10 | G/A/R | |
| Credential Exposure | <n>/10 | G/A/R | |
| Outdated Dependencies | <n>/10 | G/A/R | |
| Fail Rate Prevention | <n>/10 | G/A/R | |
| Maturity Index | <n>/10 | G/A/R | |
| Structural Weakness | <n>/10 | G/A/R | |
| Verbosity/Complexity | <n>/10 | G/A/R | |
| Unused Package | <n>/10 | G/A/R | |
| Implicit Exploitation | <n>/10 | G/A/R | |
| JSON Key / Null Pointer | <n>/10 | G/A/R | |
| Assumption Design Debt | <n>/10 | G/A/R | |

**UI Overall:** **<overall_score> / 10** (arithmetic mean of eleven vectors above)

## Scoring rules (deterministic)

| Vector | Green (8–10) | Amber (5–7) | Red (0–4) |
|--------|--------------|-------------|-----------|
| Path Traversal | No unsafe path joins with user input | Review items with file I/O | Confirmed traversal sinks |
| Credential Exposure | No hardcoded secrets | Low-risk config patterns | Secrets in source/bundle |
| Outdated Dependencies | 0 critical/high CVE | Medium CVEs with plan | Critical unwaived CVE |
| Fail Rate Prevention | No empty catch; tests green | Isolated swallowing | Widespread error masking |

Collectors: npm audit, eslint, TypeScript, bundle inspect — not heuristic Python scorers.
