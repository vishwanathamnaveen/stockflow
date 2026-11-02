# Parallel-agent file ownership

When more than one agent runs in the same repo (batch `/implement-api` (command spine), parallel slices):

- Each agent writes only under its `scope.yaml` allowlist.
- Shared files (shell, nav, global OpenAPI merge, platform config) are **forbidden** unless the user names a single owner in `docs/harness/decisions.md`.
- Additive-only for migrations: never edit an already-applied versioned migration; allocate the next unused version.
- Do not `git commit` or `git push` unless the user explicitly asks.
- Conflicts on a shared file → stop, ask, record DQ in audit.

Use this template to list forbidden paths for a program:

```
## Forbidden shared files
- <path> — owner: <agent or human>
```
