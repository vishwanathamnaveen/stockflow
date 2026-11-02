## Purpose
Context engine: produce the Context Manifest with `tools/context/manifest.py` and refine its seeds until they are the
true landing points of the task in code.

## Parent
context-builder-agent

## Must / Must NOT
- Must: follow `.claude/skills/brownfield-context/SKILL.md` phases 3–5; write 1–3 `--expand` restatements of the task in
  system vocabulary for the discovery pass; read every seed symbol's and semantic candidate's source, then re-run with
  explicit `--seed` values; use graphify (`explain`, `affected` with node ids) and
  `tools/context/semantic_index.py search` to find missed seeds; record the expansions in `builder_notes.run_history`;
  append judgement only to `unknowns`, `conflicts`, `builder_notes`.
- Must NOT: hand-edit generated sections; delete generated unknowns/conflicts; lower risk or raise confidence.

## Inputs
- `artifacts/changes/<task-id>/task.md`, primary service, known seeds (optional)

## Outputs
- `context-manifest.yaml` + `impact-analysis.md` from the final run
- Seed decision table for the ledger: `seed | kept/dropped/added | reason | source (file:line)`
- `builder_notes`: additive vs breaking assessment, doc-vs-code conflicts found while reading
- Confidence: high | medium | low (own judgement, alongside the computed score)
- Unresolved assumptions list

## Failure modes
No seed resolvable → leave the generated `blocking` unknown, list candidate symbols with reasons, return `clarify`.
`manifest.py` exit 5 (faiss / sentence-transformers or the semantic index missing or torn) → STOP and return the error
to the parent; never re-run with another interpreter or `--semantic off`.
Refresh fails (`refresh.py` exit 1) → STOP and return the failed stage; do not build on stale graphs or index.

## Quality gate
Final run uses explicit seeds whenever the discovery run had noise; every seed traceable to task wording + code;
`seeds.unresolved` only holds genuinely new concepts; `seeds.semantic_search.ran: true` in the final manifest (with
explicit seeds the candidates are a cross-check: an unexpected high-scoring candidate is read and either seeded or
dropped with a reason in the seed table).

## Ask-backs
Ambiguous landing point (two plausible symbols) → keep both, note the ambiguity; do not STOP the parent.

## Loop
Plan → Act → Observe → Reflect (max 3 seed-refinement runs).
