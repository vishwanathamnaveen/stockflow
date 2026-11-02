## Brownfield change path (starter kit)

> Why this section is here: Claude Code reads `CLAUDE.md` at the start of every session in this repo. The kit's
> rules (`.claude/rules/*.mdc`) and hooks are in Cursor's format and are only read when a command points an agent at
> them, so this section is what tells *every* session, including a plain chat with no command, that existing code
> changes only through the commands below. The commands themselves are defined in `.claude/commands/`; the full
> rules are in `.claude/rules/40-brownfield-change-governance.mdc`. Added by the starter kit's `install.py`; refresh
> it with `install.py <repo> --apply --upgrade`, and keep it.

Every requirement, bug or refactor on existing code goes through the context engine (rule 40):

1. `/setup-context` once per repo; afterwards `/refresh-context` keeps graphs and indexes fresh.
2. `/build-context "<request>"` -> `artifacts/changes/<id>/` (manifest, impact analysis, change plan).
3. Human gate per workflow (fast-track / plan-approve-execute / guarded / clarify).
4. `/implement-change <id>` -> code + tests + verification + episode.
5. `/evaluate-change <id>`; at the end of the pilot `/evaluate-pilot`.

Rules that always apply here: tools in `tools/context/` and `scripts/` produce every graph, index and manifest
(never hand-write them); only services in `brownfield.enabled_services` may be changed; no invented business rules.
Toolchain: `python scripts/setup_toolchain.py` (locked versions + the embedding model); `--check` diagnoses it.
