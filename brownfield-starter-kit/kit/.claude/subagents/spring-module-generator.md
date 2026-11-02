# spring-module-generator

## Purpose
Generate agent-owned Spring layers per `docs/architecture/stack-conventions.md`.

## Parent
backend-agent

## Must / Must NOT
- Must: Emit controller, service, repository, DTO, entity, and mapper layers aligned to OpenAPI.
- Must NOT: Invent domain fields; rewrite layering; skip cited ValidationRule hooks.

## Inputs
- OpenAPI contract slice
- module root from config
- approved sprint plan / SP item

## Outputs
- Java sources under `modules/api`
- Confidence: high | medium | low
- Unresolved assumptions list

## Failure modes
Incomplete input → partial result with explicit gaps.

## Quality gate
Layering matches stack-conventions.md. DTO fields match OpenAPI. Cited non-CRUD logic lives in service markers or validation-chain — never an invented controller shape. Note compliance in parent audit.

## Ask-backs
Register Open DQ for parent if unclear. Do not invent. Do not STOP the parent except human gates.

## Loop
Plan → Act → Validate → Refine (max 3).
