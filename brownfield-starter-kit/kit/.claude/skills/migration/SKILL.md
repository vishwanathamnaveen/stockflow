---
name: migration-mapping-and-phased-cutover
description: Additive DDL and schema mapping during /implement-api. Inventory-first; no destructive cutover in this kit.
---

# Migration (DDL)

Used by **data-agent** mode `ddl` inside `/implement-api` when persistence changes.

## Steps

1. **Inventory** existing migrations under `modules/api/.../db/migration/` — never edit applied versions.
2. **Additive only** — new Flyway/Liquibase version per change.
3. Map columns to cited story/BRD fields — no invented columns (`# AMBIGUITY` → stop).
4. schema-coverage-validator PASS before DoD.

## Must NOT

- DROP TABLE unless story AC quotes it explicitly.
- Destructive cutover (not in this kit — requires explicit human gate and cutover plan).

## Subagents

`schema-migration-generator`, `migration-baseline-inventory`, `schema-coverage-validator`
