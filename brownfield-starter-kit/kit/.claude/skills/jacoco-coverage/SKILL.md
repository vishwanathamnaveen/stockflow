---
name: jacoco-coverage
description: Run JaCoCo coverage for the API module, interpret line/branch gaps, and recommend unit tests. Use when improving API coverage or reporting metrics.
---

# JaCoCo Coverage

## Run
Use the product's Java toolchain (see `config.yaml` `modules.api`). Typical:

```bash
cd <api-module-root>
mvn test jacoco:report
```

Parse `target/site/jacoco/jacoco.xml` for LINE / BRANCH / INSTRUCTION counters.

## Priority for branch gaps
1. Validation / domain rules (one test per branch)
2. Application services
3. Parsers / calculators / adapters

## Gates
`.claude/config.yaml` → `quality_gates.api_unit_line_coverage_min` and `api_unit_branch_coverage_target`. Do not lower them.

Run after unit/IT tests; use with live stack when IT probes run (skill: `quality`).

## Subagent
`.claude/subagents/coverage-analyzer.md`
