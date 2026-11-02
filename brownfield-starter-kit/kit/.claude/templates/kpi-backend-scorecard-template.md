# Backend KPI Scorecard — <module> — Sprint <sprint_number>

## Metadata

| Field | Value |
|-------|-------|
| Run ID | <run_id> |
| Validation scope | sprint / overall |
| Sprint number | <sprint_number> (omit for overall-only) |
| Module | <modules.api> |
| Overall score | <overall_score> / 10 |
| Overall status | Green / Amber / Red |
| Generated (UTC) | <timestamp> |

## Scorecard (0–10)

| Metric | Score | Status | Evidence summary |
|--------|-------|--------|------------------|
| Security | <n>/10 | G/A/R | |
| Readability | <n>/10 | G/A/R | |
| Requirement coverage | <n>/10 | G/A/R | |
| Test coverage | <n>/10 | G/A/R | |
| Defect density | <n>/10 | G/A/R | |
| Maintainability | <n>/10 | G/A/R | |
| Adherence to guidelines | <n>/10 | G/A/R | |
| Documentation | <n>/10 | G/A/R | |

**Backend Overall:** **<overall_score> / 10** (arithmetic mean of eight metrics above)

## Scoring rules (deterministic)

| Metric | Green (8–10) | Amber (5–7) | Red (0–4) |
|--------|--------------|-------------|-----------|
| Security | 0 critical/high; auth configured | Medium findings documented | Critical unwaived or no security config |
| Readability | Formatter/linter clean | Minor style drift | Widespread readability blockers |
| Requirement coverage | 100% in-scope stories traced | Partial gaps with owners | Critical stories untraced |
| Test coverage | JaCoCo line ≥ 80% (critical domains) | 60–79% | < 60% or no tests |
| Defect density | ≤ 1.0 blocker+critical / KLOC | 1.0–3.0 / KLOC | > 3.0 / KLOC |
| Maintainability | Complexity within limits | Isolated hotspots | Systemic complexity debt |
| Adherence to guidelines | REST conventions met | Documented exceptions | Violations on security/API paths |
| Documentation | OpenAPI + README complete | Minor gaps with owner | Missing contract docs |

Evidence must come from toolchain collectors, not heuristic LLM scores.
