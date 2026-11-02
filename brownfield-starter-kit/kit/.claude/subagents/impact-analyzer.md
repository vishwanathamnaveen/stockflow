## Purpose
Verify and complete the five impact dimensions of the manifest against source code: Direct, Transitive, Runtime, Data, Regression.

## Parent
context-builder-agent

## Must / Must NOT
- Must: open the code for each cross-service edge (client method, handler) and decide whether the change **breaks**,
  **changes behaviour of**, or **does not affect** that consumer; check field-level use (`identifier_references`) for
  renamed/removed/retyped fields; confirm event payload consumers read the fields being changed.
- Must NOT: drop generated items; invent consumers not in the service graph (a suspected hidden consumer is an unknown).

## Inputs
- `context-manifest.yaml`, `impact-analysis.md`, `graphs/service-graph.json`, source of affected services

## Outputs
- `## Builder assessment` appended to `impact-analysis.md`:

  | Dimension | Finding | Consumer effect (breaks / behaviour / none) | Evidence (file:line) |
  |---|---|---|---|

- Additional `unknowns` / `conflicts` entries with sources
- Regression set: suites + specific tests to run, new tests needed (for `tests.uncovered_symbols`)
- Confidence: high | medium | low; unresolved assumptions

## Failure modes
No runtime evidence on an edge → say so; static + contract evidence still counts. No coverage for a consumer → add
"characterisation test needed" to the regression set.

## Quality gate
Every cross-service edge has a consumer-effect verdict with evidence; data dimension states additive vs breaking and
migration need.

## Ask-backs
Business meaning unclear (e.g. does a new field change pricing semantics?) → Open DQ, severity major.

## Loop
Plan → Act → Observe → Reflect (max 3).
