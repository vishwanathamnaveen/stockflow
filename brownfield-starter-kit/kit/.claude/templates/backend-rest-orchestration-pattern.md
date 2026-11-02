# Backend REST Orchestration Pattern — {{SLICE}}

> Layering and flow for `/implement-api`. Extend existing controllers/services — do not duplicate parallel implementations.

| Field | Value |
|-------|-------|
| **Slice / feature** | {{name}} |
| **Stack** | java (Spring) / python (per config) |
| **Module root** | `${modules.api}` or `${modules.source}` |
| **OpenAPI** | `contracts/openapi/{{file}}.yaml` |
| **Story refs** | {{SP-xxx, FR-xxx, BR-xxx}} |

## Layer responsibilities

| Layer | Package / path | Must do | Must NOT |
|-------|----------------|---------|----------|
| Controller | `.../web/` or `.../api/` | HTTP mapping, status codes, input DTO binding | Business rules, direct DB |
| Service | `.../service/` | Business logic, transactions, orchestration | HTTP concerns |
| Repository | `.../repository/` | Persistence queries | Business rules |
| Domain / entity | `.../domain/` | Entity, value objects | Framework annotations (keep thin) |
| DTO / mapper | `.../dto/`, MapStruct or equivalent | OpenAPI ↔ internal shapes | Leak entities to API |
| Exception handler | `@ControllerAdvice` or equivalent | Central error envelope | Per-controller try/catch soup |

## Request flow (happy path)

```text
Client → Controller → Service (@Transactional on writes) → Repository → DB
              ↓
         Response DTO ← Mapper ← Domain/Entity
```

## Cross-cutting concerns

| Concern | Implementation | Cite |
|---------|----------------|------|
| AuthN | | NFR / BR |
| AuthZ | method-level / route-level | |
| Validation | Bean Validation / pydantic at boundary | OpenAPI required fields |
| Logging | structured; no PII | |
| Correlation ID | propagate from header | api-contract-template |
| Idempotency | key header on POST where required | |

## Error mapping

| Exception / condition | HTTP | error.code | User message source |
|-----------------------|------|------------|---------------------|
| Validation failure | 400 | VALIDATION_ERROR | centralized |
| Not found | 404 | NOT_FOUND | |
| Business rule (BR-xxx) | 422 | cite BR | cited microcopy only |

## Transaction boundaries

- **Write operations:** `@Transactional` on service public methods
- **Read-only:** `@Transactional(readOnly = true)` where applicable
- **No partial commits:** rollback on any unchecked business failure

## Test alignment

| Layer | Test type | Template / pattern |
|-------|-----------|-------------------|
| Service | unit | `agent-owned JUnit tests` or pytest |
| Controller | slice / MockMvc | IT template |
| Contract | OpenAPI verify | api-agent gate |

## Files to create or extend (checklist)

- [ ] Controller — operationIds match OpenAPI
- [ ] Service interface + impl
- [ ] Repository
- [ ] DTOs + mapper
- [ ] Flyway / migration if persistence changed
- [ ] Unit + IT tests mapped to TC- ids
- [ ] Audit + test-results artifact

**Output path:** Reference in `artifacts/audit/{{date}}-implement-api-{{task}}.md` — pattern doc lives in templates (not copied per slice unless team maintains slice notes under `docs/implementation/`).
