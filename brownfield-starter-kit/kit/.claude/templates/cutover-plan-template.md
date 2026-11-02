# Cutover Plan — {{SYSTEM_OR_MIGRATION}}

> **Human gate:** data-owner sign-off required before destructive apply. data-agent owns additive DDL; destructive steps need quoted story AC.

| Field | Value |
|-------|-------|
| **Plan ID** | CUT-{{YYYYMMDD}}-{{slug}} |
| **Status** | Draft / Pending sign-off / Approved / Executed / Rolled back |
| **Owner** | data-agent |
| **Environment** | {{prod-like / staging}} |
| **Cutover window** | {{start}} – {{end}} UTC |
| **Story / AC refs** | {{ids with destructive permission}} |

## Objectives

- **Source system(s):**
- **Target system(s):**
- **Success criteria:**

## Scope

| In scope | Out of scope |
|----------|--------------|
| | |

## Pre-cutover checklist

| # | Task | Owner | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | Backup verified | data owner | | |
| 2 | Migration scripts reviewed (forward-only) | | | |
| 3 | Reconciliation dry-run | | | `migration-reconciliation-template` |
| 4 | Rollback tested on staging | | | |
| 5 | **Data-owner sign-off** | | | |

## Mapping summary

| Source entity | Target entity | Transform rule | Volume estimate |
|---------------|---------------|----------------|-----------------|
| | | cite mapping doc | |

## Execution steps

| Step | Action | Duration est. | Rollback trigger |
|------|--------|---------------|------------------|
| 1 | Freeze writes | | |
| 2 | Final incremental sync | | |
| 3 | Validation queries | | |
| 4 | DNS / traffic switch | | |

## Validation

| Check | Query / method | Expected | Actual |
|-------|----------------|----------|--------|
| Row counts | | | |
| Sample records | | | |
| API smoke | | | |

## Rollback plan

1. 
2. 
**Max acceptable rollback time:**

## Communication

| Audience | Message | When | Channel |
|----------|---------|------|---------|
| | | | |

## Post-cutover

| Task | Owner | Due |
|------|-------|-----|
| Reconciliation report | | |
| Decommission source (if applicable) | | |

**Output path:** `docs/data-migration/{{date}}-cutover-plan.md` or `artifacts/migration/{{date}}-cutover-plan.md`
