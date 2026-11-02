# Decision ledger — {{TASK_ID}}

Append-only. One row per decision; supersede with a new row, never edit an old one. No secrets or PII.

| # | Date | Phase | Decision | Reason / evidence | By |
|---|---|---|---|---|---|
| 1 | {{YYYY-MM-DD}} | intake | Task typed `{{type}}`, primary service `{{service}}` | task.md, service_scores | context-builder-agent |
| 2 | | context | Seed `{{symbol}}` kept / dropped / added | {{file:line, reason}} | context-builder-agent |
| 3 | | risk | Workflow `{{selected}}` (computed `{{computed}}`) | {{factors / escalation reason}} | risk-workflow-selector |
| 4 | | gate | change-plan **Approved** | — | {{human name}} |
| 5 | | implement | {{step done / scope drift / unknown resolved}} | {{diff, test id}} | change-agent |
| 6 | | verify | Judge {{PASS/FAIL}}, checks {{green/red}}, repair iteration {{n}}/3 | verification.md | change-judge |
| 7 | | close | Outcome `{{success/failed/abandoned}}`; episode recorded; graphs refreshed | episodes.jsonl | decision-ledger-writer |

## Lessons for the next change in these files

- {{e.g. a consumer service caches this entity; any change to a cached field must publish <entity>.updated}}
