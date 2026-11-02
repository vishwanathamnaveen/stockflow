---
description: Prevent invented behavior
alwaysApply: true
---

# Behavior Provenance and Anti-Invention

Every non-trivial behavior statement must carry: `behavior_id`, `statement`, `source_path`, `source_locator`, `confidence` (`explicit` | `derived` | `assumption`).

If sources are silent: register `ASSUMPTION-<id>` pending approval. Do not mark Ready/Done with pending assumptions.

Prohibited without explicit source: new domain rules, user-facing microcopy, error semantics, authz decisions, merge/dedupe policy.

Conflicts: `BLOCKED_CONFLICT` and escalate. Precedence: approved story/BRD → approved UX → approved API contract → existing implementation.
