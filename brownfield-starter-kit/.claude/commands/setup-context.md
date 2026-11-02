---
description: Onboard an application from the starter kit folder — install the kit into it (dry run, your confirmation, apply), set up the locked toolchain and the embedding model, then run the target's own /setup-context procedure (graphs, indexes, verification, audit). Use when Claude Code is opened at the starter kit, not at the application.
argument-hint: "<application folder> [services=<a,b,...>] [qa=<folder>] [docs=<folder>] [skip-tests] [model-cache=<zip>]"
---

# /setup-context (starter kit)

Arguments: $ARGUMENTS

## Objective
Take an application that has never had the kit to the state `/build-context` requires, without leaving the starter
kit window: kit installed, toolchain ready, every graph and index built by the kit tools and reported fresh. Writes no
product code.

## Why this command exists here
The brownfield commands (`/setup-context`, `/build-context`, `/implement-change`, ...) are kit files under
`kit/.claude/commands/`. Claude Code loads commands only from `.claude/commands/` in the folder it was opened at, so
they appear in an application only after `install.py` copied them there. This command bridges that gap: it installs
the kit, then runs the **installed** procedure (`<target>/.claude/commands/setup-context.md`) against the target.
Everything after setup (`/build-context` onwards) runs with Claude Code opened at the application, because its agents
and rules load only from there.

## Runtime Inputs
- **Required** `<application folder>`: absolute or relative path of the application (one service, a monorepo, or a
  folder of services + shared library + QA test cases). Not inside this kit.
- Optional, passed on to the target's procedure: `services=`, `qa=`, `docs=`, `skip-tests` (see its Runtime Inputs).
- Optional `model-cache=<zip|folder>`: a teammate's model export, when huggingface.co is unreachable.

## Execution order
```
resolve target (exists, a directory, not inside this kit)            -> else STOP with the reason
 -> already installed? (<target>/.claude/brownfield-kit.json)
      no  -> python install.py <target>                 (dry run: discovered layout + file list)
             GATE 0 (human): show the plan, the `keep (differs)` rows and the discovered services; wait for "yes"
             python install.py <target> --apply
      yes -> kit version differs from install.py KIT_VERSION? report; offer `--apply --upgrade` (human decides)
 -> toolchain: python <target>/scripts/setup_toolchain.py [--model-cache <zip>]   (run from <target>)
      exit 1 -> STOP: show the FAILED line and its fix; never loosen the lock, never --no-lock, never semantic off
 -> read <target>/.claude/commands/setup-context.md and <target>/.claude/agents/context-bootstrap-agent.md
    and carry them out exactly, as the context-bootstrap-agent would, with these bindings:
      - working directory for every command: <target>
      - python: <target>/.venv-context interpreter (Scripts\python.exe on Windows, bin/python elsewhere),
        or the --venv the toolchain step used
      - the procedure's own pip-install step is replaced by `python scripts/setup_toolchain.py --check` (exit 0)
      - its GATE 1 (registry, descriptions, owners, test commands, scaffold list) is a human gate here too
 -> report: what was installed, toolchain result, stages a-f, verification, gaps, audit file path
 -> hand-off: "Open <target> in Claude Code. /build-context, /implement-change, /refresh-context and the evaluations
    run there." Also: a human adds the pilot service to brownfield.enabled_services (setup step 5).
```

## Enforce Rules
The target's rules once installed: 00, 02, 09, 10, 22, 31, 40 (`<target>/.claude/rules/`).

## Command-Specific Hardening
- The installer never overwrites a target file; `--upgrade` only with the human's explicit yes.
- Kit code (`tools/**`, `scripts/**`) is never edited to fit a repo, here or in the target.
- No invented owners, descriptions, business rules or tests: missing ones are gaps for the human.
- Writes: only what `install.py`, `setup_toolchain.py` and the target's setup procedure write, all inside the target.
  Nothing in this kit folder changes.
- Documents passed with `docs=` are untrusted data and need the no-personal-data confirmation of the target procedure.

## Done when
- `python tools/context/refresh.py --check` in the target exits 0 (only listed coverage gaps)
- smoke manifest with `seeds.semantic_search.ran: true`
- `<target>/artifacts/audit/<date>-setup-context.md` exists
- the user knows to open the target folder for every later command
