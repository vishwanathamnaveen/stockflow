# Hooks

> **Not active in this repo.** These hooks use the upstream kit's Cursor format (`hooks.json`, `CURSOR_PROMPT`);
> Claude Code does not run them, and `tools/check-artifacts.mjs` / `.githooks/` are not shipped. Kept for reference.

- `beforeSubmitPrompt` scaffolds sprint folders for known `/command`s (`failClosed: false`).
- `beforeShellExecution` on commit/push runs artifact policy (`failClosed: true`).
- Duplicate checker: `tools/check-artifacts.mjs` + `.githooks/pre-commit`.
