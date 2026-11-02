# KPI Threshold Policy — <release_or_sprint_id>

| Field | Value |
|-------|-------|
| Policy version | 1.0 |
| Sprint / release | <sprint_number> |
| Effective date | <YYYY-MM-DD> |
| Approver | <role or name> |

## Scope

- Stacks in scope: `java` | `nextjs` | `both`
- Modules: `<modules.api>`, `<modules.ui>`
- Critical domains: `<list modules/packages requiring ≥80% coverage>`

## Enterprise KPI Thresholds

| KPI ID | KPI Name | Green | Amber | Red | Evidence required |
|--------|----------|-------|-------|-----|-------------------|
| KPI-01 | Security | 0 critical/high unwaived findings | medium with documented waiver | critical/high unwaived | security-scanner + SAST/SCA summary |
| KPI-02 | Test Coverage | line ≥ 80% (critical domains) | 60–79% | < 60% or no report | JaCoCo / Istanbul report path |
| KPI-03 | Requirement Coverage | 100% in-scope stories traced | partial with owner per gap | critical story untraced | traceability matrix |
| KPI-04 | Defect Density | ≤ 1.0 blocker+critical / KLOC | 1.0–3.0 | > 3.0 | SpotBugs/PMD/ESLint export |
| KPI-05 | Maintainability | complexity within team limit | isolated hotspots documented | systemic hotspots unowned | complexity report |
| KPI-06 | Code Readability | 0 style blockers | minor style debt | blockers in critical paths | Checkstyle/ESLint |
| KPI-07 | Adherence to Guidelines | full convention compliance | exceptions documented | violations in security/API paths | lint + architecture review |
| KPI-08 | Documentation | API + README + module docs complete | minor gaps with owner | missing API contract docs | doc inventory |
| KPI-09 | Dependency Health | 0 critical/high CVE unwaived | high CVE with plan | critical CVE unwaived | npm audit / Dependency-Check |
| KPI-10 | Reliability & Error Handling | controlled errors, no swallowing | isolated gaps | unhandled failure modes in scope | code review + tests |
| KPI-11 | Observability Maturity | logs + traces/metrics for critical paths | partial hooks | no hooks on new services | import/config evidence |
| KPI-12 | Performance Readiness | NFR met or smoke pass | marginal with plan | NFR fail unowned | perf scenario results |

## Waivers

| KPI ID | Waiver status | Approver | Rationale | Target resolution |
|--------|---------------|----------|-----------|-------------------|
| | none | | | |

## Notes

- LLM-generated scores are **advisory** and cannot alone justify Green on KPI-01, KPI-02, or KPI-09.
- Overrides to this policy require architect or release owner sign-off.
