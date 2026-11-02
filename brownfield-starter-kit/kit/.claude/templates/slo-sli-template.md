# SLO / SLI — {{SERVICE_NAME}}

> From sre-agent. Golden signals + error budget. Do not invent baselines without measurement evidence.

| Field | Value |
|-------|-------|
| **Service** | {{name}} |
| **Tier** | critical / standard / internal |
| **Owner** | {{team}} |
| **Last reviewed** | {{YYYY-MM-DD}} |
| **Document status** | Draft / Active |

## Service description

- **User-facing purpose:**
- **Dependencies:**
- **Critical journeys:** (link AC or runbook)

## SLIs (indicators)

| SLI ID | Name | Measurement | Data source |
|--------|------|-------------|-------------|
| SLI-1 | Availability | successful requests / total | APM |
| SLI-2 | Latency | p95 response time | APM |
| SLI-3 | Error rate | 5xx / total | logs |
| SLI-4 | Saturation | CPU/memory/queue depth | infra metrics |

## SLO targets

| SLO ID | SLI | Target | Window | Error budget |
|--------|-----|--------|--------|--------------|
| SLO-1 | Availability | 99.9% | 30d rolling | 43.2 min/month |
| SLO-2 | Latency p95 | < 500ms | 30d | |

## Alerting

| Alert | Condition | Severity | Runbook |
|-------|-----------|----------|---------|
| | SLO burn rate > 2x | page | `docs/runbooks/…` |

## Dashboards

| Dashboard | URL / path | Audience |
|-----------|------------|----------|
| | | on-call |

## Exclusions

- **Maintenance windows:**
- **Non-user-facing endpoints excluded:**

## Review history

| Date | Change | Approver |
|------|--------|----------|
| | | |

**Output path:** `docs/sre/slo-{{service-slug}}.md`
