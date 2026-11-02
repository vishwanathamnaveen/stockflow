---
description: Brownfield — bring system intelligence (code graphs, service graph, semantic index) up to date with the working tree using the deterministic tools, and, for a task, check the change stayed inside its approved scope. Run after the last code edit and before final validation.
argument-hint: "[<task-id>] [--tests]"
---

# /refresh-context

Arguments: $ARGUMENTS

## Objective
Make the context the agents read match the code as it is now, and prove it. All guarantees (lock, change detection,
fail-fast stages, retry when inputs move, post-refresh verification, source-state digest) live in
`tools/context/refresh.py`; this command only runs it and reports. **Never edit graph JSON, embeddings or index files
by hand** — a fact that a tool did not compute is not a fact.

## When to use
- Inside `/implement-change`: after the last code edit, **before** required checks and change-judge; again after any
  repair-loop edit.
- Before `/build-context` when `refresh.py --check` exits 2 (the builder skill already does this).
- After pulling or switching branches, when you are about to rely on search or a manifest.
- After editing anything the context is built from outside `/implement-change`: code, `docs/business-rules.md`,
  `contracts/**`, `config/**`, `knowledge/**`.

Nothing triggers a refresh on its own: the kit's hooks are Cursor-format and do not run in Claude Code, and CI does
not check freshness yet. A manual edit stays invisible to the graphs and index until the next `refresh.py --check`.

## Runtime Inputs

### Optional
- `task-id` — also run the post-change scope check for `artifacts/changes/<task-id>/`
- `--tests` — re-run the changed services' tests first (default **on** inside `/implement-change`: after a code edit the
  per-test coverage still describes the old line numbers, so enrichment would map tests to the wrong symbols)

## Execution order
```
python tools/context/refresh.py --stale [--tests]
  exit 0 → continue          exit 1 → STOP: report the failed stage verbatim; never claim success
  exit 3 → another refresh holds the lock: wait for it, then run again (never delete the lock by hand)
[task-id] python tools/context/manifest.py --verify-scope <task-id>
  exit 0 → within approved scope
  exit 4 → scope grew: STOP → scope-change request (rule 40.4):
           python tools/context/manifest.py --amend <task-id> --add-seed <...> --reason "<scope-check.yaml evidence>"
           a stricter amended workflow or risk voids earlier approvals
report (below)
```

## What it rebuilds (decided by the tool, not by the agent)
| Changed | Rebuilt |
|---|---|
| a service `.py` file (modified / new / deleted), engine version or build config | graphify + enrichment for that service + overall graph |
| only `docs/business-rules.md`, coverage, or the topics a service publishes | enrichment only (seconds) |
| config, contracts, service-package code | service graph (it is regenerated on every refresh anyway: cheap, and enrichment reads it) |
| any document the index would now build differently (or the embedding model) | changed/new documents re-embedded, removed ones dropped; the rest reused (model not loaded when nothing changed) |
| a file under `knowledge/` added / changed / removed | that file re-extracted and re-embedded (knowledge base, `graphs/kb/`) |

Order: service graph → graphify → enrichment → semantic index → knowledge base; the first failing stage stops the
rest. Traces never make anything stale (runtime evidence proves presence, not absence). The semantic index and the
knowledge base are **required**: `unavailable` (faiss / sentence-transformers not installed) is stale, and the build
stage fails (exit 1) until `python scripts/setup_toolchain.py` (or `--check` to diagnose) is run for the same `python`.

## Required Output (in the reply, and in `verification.md` inside `/implement-change`)
- snapshot digest, base commit, `working_tree` (from the tool's last lines; also `var/context/snapshot.json`)
- services rebuilt with graphify / enrich-only / tests run
- semantic index: documents, embedded, reused, removed
- scope check: within scope, or what grew (`scope-check.yaml`)

## Rules
- A pre-commit refresh has no commit SHA of its own: report `source_state_digest` + `base_commit` + `working_tree`.
  Do not amend commits to stamp a SHA into generated files.
- If code changes after this command (review, repair loop, manual edit), run it again before validating.
- Generated artifacts are not committed by this command. Policy: graph JSON may be committed; `graphs/semantic/`
  (FAISS, vectors) is a local build artifact (git-ignored). Shared snapshots are CI's job.

## Definition of Done
- [ ] `refresh.py --stale` exit 0 (post-refresh verification passed)
- [ ] Scope check exit 0, or a scope-change request raised
- [ ] Snapshot digest + counts reported
