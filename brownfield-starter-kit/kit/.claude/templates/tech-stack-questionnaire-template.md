# Tech-stack questionnaire — {{SESSION_ID}}

> `/propose-architecture`. Log Q&A to `artifacts/architecture/<date>-questionnaire-log.md`.

| Field | Value |
|-------|-------|
| **Date** | {{YYYY-MM-DD}} |
| **Operator** | {{name or role}} |

| # | Question | Recommended (recommended default) | Your choice | Source if pre-filled |
|---|----------|------------------------------|-------------|----------------------|
| 1 | Backend framework? | Java 21 + Spring Boot 3.x | | |
| 2 | UI framework? | Next.js 14+ App Router + TypeScript | | |
| 3 | API style? | REST + OpenAPI 3.1 | | |
| 4 | Persistence? | PostgreSQL + JPA/Flyway | | |
| 5 | UI data fetching? | Typed fetch client from OpenAPI | | |
| 6 | Test layers? | JUnit 5 + Vitest + Playwright | | |
| 7 | Module layout? | `modules/api` + `modules/ui` monorepo | | |
| 8 | Auth pattern (high level)? | JWT bearer (detail deferred) | | |

## Suggested config.yaml bindings (proposal only)

```yaml
modules:
 api: modules/api
 ui: modules/ui
 openapi: contracts/openapi/{{service}}-v1.yaml
```
