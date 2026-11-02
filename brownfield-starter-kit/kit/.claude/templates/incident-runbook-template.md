# Incident Runbook — {{SERVICE_OR_ALERT}}

> Owned by sre-agent. Do not invent baselines — cite SLO doc or observability evidence.

| Field | Value |
|-------|-------|
| **Runbook ID** | RB-{{slug}} |
| **Service** | {{name}} |
| **Alert / symptom** | {{pager condition}} |
| **Severity default** | SEV-1 / SEV-2 / SEV-3 |
| **Last reviewed** | {{YYYY-MM-DD}} |
| **Owner** | {{on-call rotation}} |

## Overview

- **User impact:**
- **Dependencies:**
- **SLO at risk:** (cite `docs/sre/slo-…`)

## Detection

| Signal | Source | Threshold |
|--------|--------|-----------|
| Error rate | | |
| Latency p95 | | |
| Saturation | | |

## Immediate actions (first 15 min)

| # | Action | Owner | Done |
|---|--------|-------|------|
| 1 | Acknowledge alert | on-call | |
| 2 | Check dashboard | | |
| 3 | Assess blast radius | | |
| 4 | Communicate status | | |

## Diagnosis steps

| Step | Check | Expected | If abnormal |
|------|-------|----------|-------------|
| 1 | Health endpoint | 200 | → escalation path B |
| 2 | Recent deploys | | → rollback section |
| 3 | Dependency status | | | |

## Mitigation

### Rollback

1. 
**Command / pipeline:**

### Scale / failover

1. 

### Data fix (if applicable)

- **Requires data-owner approval:** yes/no

## Escalation

| Condition | Contact | Method |
|-----------|---------|--------|
| SEV-1 > 30 min | | |
| Data integrity | data owner | |

## Post-incident

- [ ] Timeline in incident ticket
- [ ] Update runbook if gap found
- [ ] Link to `docs/harness/decisions.md` if policy change

**Output path:** `docs/runbooks/{{slug}}.md`
