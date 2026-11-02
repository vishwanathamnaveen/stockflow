# Test package review — {{scope}}

Human gate after `/expand-test-coverage` coverage PASS. Agents set **Pending Approval** only. Orchestrator **refuses** `/run-tests` until a human sets **Approved** (or a dated waiver exists in `docs/harness/decisions.md`).

| Field | Value |
|-------|-------|
| Scope | {{sprint item / story pack / bounded context}} |
| Date (package) | YYYY-MM-DD |
| Coverage gate | `docs/test-cases-br-coverage.md` |
| Coverage status | PASS |
| Coverage ratio | mapped / in-scope (percent) |
| Cases | `docs/test-cases.md` |
| Traceability matrix | `docs/test-matrix.md` |
| Intake manifest | `artifacts/test-intake/<date>-manifest.json` or N/A |
| **Approval** | Pending Approval \| Approved |
| Approver | (human name / role — agents leave blank) |
| Approval date | (human) |

## Package checklist (agent-filled)

- [ ] Coverage Status PASS
- [ ] Completeness validator PASS (case bodies)
- [ ] Step-quality validator PASS (case bodies)
- [ ] Untrusted intake clean or skipped (trusted-only)
- [ ] Manual UAT catalog was not generated or refreshed

## Human notes

- 
