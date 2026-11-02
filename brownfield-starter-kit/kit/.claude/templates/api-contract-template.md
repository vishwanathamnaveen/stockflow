# API Contract — {{SERVICE_OR_SLICE}}

> Design-time contract notes before or alongside OpenAPI. Authoritative runtime contract is `contracts/openapi/{{file}}.yaml`. Do not invent fields, error codes, or semantics not cited in BRD/story pack.

| Field | Value |
|-------|-------|
| **Service / slice** | {{name}} |
| **OpenAPI file** | `contracts/openapi/{{file}}.yaml` |
| **Version** | {{semver or draft}} |
| **Status** | Draft / Review / Approved |
| **Owner agent** | api-agent |
| **Story / FR refs** | {{SP-xxx, FR-xxx}} |
| **Last synced** | {{YYYY-MM-DD}} (OpenAPI ↔ DTO verify) |

## Scope

- **In scope operations:**
- **Out of scope:**
- **Consumers:** (UI, batch, external)

## Conventions

| Topic | Rule |
|-------|------|
| Base path | `/api/v{{n}}` |
| Auth | Bearer JWT / API key / session — cite NFR |
| Idempotency | Required on: {{methods/operations}} |
| Pagination | cursor / offset — max page size |
| Correlation | `X-Correlation-Id` required |
| Date/time | ISO-8601 UTC |
| Money / decimals | string decimal / integer cents — cite BR |

## Standard envelope

### Success (2xx)

```json
{
  "data": {},
  "meta": { "correlationId": "", "timestamp": "" }
}
```

### Error (4xx/5xx)

```json
{
  "error": {
    "code": "DOMAIN_SPECIFIC_CODE",
    "message": "User-safe message",
    "details": [],
    "correlationId": ""
  }
}
```

| HTTP | When | error.code examples |
|------|------|---------------------|
| 400 | Validation failure | `VALIDATION_ERROR` |
| 401 | Unauthenticated | `UNAUTHORIZED` |
| 403 | Forbidden | `FORBIDDEN` |
| 404 | Missing resource | `NOT_FOUND` |
| 409 | Conflict / duplicate | `CONFLICT` |
| 422 | Business rule violation | cite BR-xxx |
| 500 | Unexpected server error | `INTERNAL_ERROR` |

Do not invent error semantics — cite BRD or register DQ-xxx.

## Operations catalog

| operationId | Method | Path | Summary | AuthZ | Idempotent | FR/BR refs |
|-------------|--------|------|---------|-------|------------|------------|
| | GET | | | | | |

## Request / response sketches

### {{operationId}}

- **Request body:** (schema name, required fields)
- **Response 200:** (schema name)
- **Negative cases:** (mandatory — auth, validation, business rule)

## Compatibility and versioning

| Change type | Breaking? | Policy |
|-------------|-----------|--------|
| Add optional field | No | Allowed in minor |
| Remove field | Yes | Major + deprecation period |
| Rename field | Yes | Major or alias period |
| Error code change | Maybe | Document in changelog |

## DTO / persistence alignment

| OpenAPI schema | DTO class | Entity / table | Notes |
|----------------|-----------|----------------|-------|
| | | | |

## Verification checklist (api-agent gate)

- [ ] OpenAPI validates (spectral / linter)
- [ ] Every operation cites FR/BR or DQ
- [ ] Negative cases documented per write/validation rule
- [ ] OpenAPI ↔ DTO sync recorded in audit
- [ ] No secrets in examples

**Output path:** `docs/api/{{slice}}-contract-notes.md` and `contracts/openapi/{{file}}.yaml`
