---
description: Contract-first API governance
globs: "contracts/**/*"
alwaysApply: false
---

# API Contracts

- OpenAPI (or GraphQL SDL) is the source of truth for request/response shapes.
- Version contracts; document error matrix and envelope policy.
- `api-agent` has two ordered gates: (1) design/lint/examples (2) OpenAPI↔DTO sync during `/implement-api`. Do not skip verify; do not redesign silently during implement.
- No stack traces to clients.
