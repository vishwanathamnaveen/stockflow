# CLAUDE.md — brownfield starter kit (this folder is the kit, not an application)

This folder is the **source** of the kit. Nothing here is analysed or changed by the context engine; it is copied
into an application by `install.py`. Never run the context tools (`tools/context/*.py`, `scripts/*.py`) with this
folder as the repo root, and never point `install.py` at a folder inside it.

## Commands available when Claude Code is opened here

| Command | Does |
|---|---|
| `/setup-context <application folder>` | install the kit (dry run, your OK, apply), toolchain, then the application's own setup procedure: graphs, indexes, verification, audit |
| `/install-kit <application folder> [upgrade]` | install or upgrade the kit + toolchain only |
| `/toolchain-doctor <application folder> [repair]` | diagnose Python / package / Hugging Face model problems; repair with your OK |

The change commands (`/build-context`, `/implement-change`, `/refresh-context`, `/evaluate-change`,
`/evaluate-pilot`) are **not** run from here. Their definitions live in `kit/.claude/commands/` and become active in an
application after installation: open the application folder in Claude Code and run them there.

## Layout

| Path | What |
|---|---|
| `install.py` | copies `kit/` into an application; dry run by default, never overwrites |
| `kit/.claude/` | what the application gets: commands, agents, subagents, rules, skills, templates |
| `kit/tools/context/`, `kit/scripts/` | the context engine and scripts (incl. `setup_toolchain.py`) |
| `kit/scaffold/` | inputs created only when missing; `requirements-context.txt` + `constraints-context.txt` (the toolchain lock) |
| `docs/`, `checklists/` | team guides, copied to `docs/context-engine/starter-kit/` in the application |

## Editing the kit
- The toolchain lock (`kit/scaffold/constraints-context.txt`) changes only after the whole toolchain was re-verified
  together (setup_toolchain.py in a fresh venv, reference tests); bump `KIT_VERSION` in `install.py` with it.
- Changes under `kit/tools/context/` or `kit/scripts/` need the kit self-test (`docs/03-EVALUATION.md` section 4).
