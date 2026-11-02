# Migration Reconciliation — {{CUTOVER_OR_MIGRATION}}

> Post-migration or dry-run row/column reconciliation. data-agent + cutover human gate.

| Field | Value |
|-------|-------|
| **Reconciliation ID** | REC-{{YYYYMMDD}}-{{slug}} |
| **Migration plan** | {{cutover plan path}} |
| **Environment** | staging / prod |
| **Run date** | {{YYYY-MM-DD}} |
| **Status** | Pass / Fail / Partial |

## Scope

| Source | Target | Key columns |
|--------|--------|-------------|
| | | |

## Row counts

| Entity | Source count | Target count | Delta | Tolerance | Pass |
|--------|--------------|--------------|-------|-----------|------|
| | | | | 0 | |

## Hash / checksum samples

| Sample set | Source hash | Target hash | Match |
|------------|-------------|-------------|-------|
| random 1k rows | | | |

## Column mapping validation

| Column | Nulls source | Nulls target | Domain violations |
|--------|--------------|--------------|-------------------|
| | | | |

## Exceptions

| ID | Description | Severity | Resolution |
|----|-------------|----------|------------|
| | | | |

## Sign-off

| Role | Name | Date | Accept reconciliation |
|------|------|------|----------------------|
| Data owner | | | yes/no |

**Output path:** `docs/data-migration/{{date}}-reconciliation.md` or `artifacts/migration/{{date}}-reconciliation.md`
