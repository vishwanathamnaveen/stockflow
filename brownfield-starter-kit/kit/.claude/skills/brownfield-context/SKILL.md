---
name: brownfield-context
description: Build and refine a Context Manifest (code graph + service graph + tests + knowledge + config + history + runtime + memory) for a task on existing code; used by /build-context and checked by /implement-change.
---

# Brownfield context

## When to use

- `/build-context` — context-builder-agent and its subagents, for every requirement, bug fix, feature or refactor.
- `/implement-change` — change-agent re-checks freshness and scope drift against the manifest.

> Examples use a hypothetical order system: a Python service (`orders`, `domain.update_order`) and a Java/Spring one
> (`OrderServiceImpl.approve`); substitute your own. The code can be in any language the kit reads (Python, Java, Kotlin, C#,
> TypeScript, JavaScript, Go, Ruby, PHP, Rust, Scala, Swift, Groovy, C/C++); seeds are written the same way for all.

## System intelligence (what each graph answers)

| Graph | Question | Source | Tool |
|---|---|---|---|
| Code graph | If this code changes, what else in the service is affected? | `<service path>/graphify-out/graph.json` (graphify) + symbol index (lang_python.py / lang_treesitter.py) | `tools/context/manifest.py`; `graphify explain/affected <graph_node> --graph …` |
| Overall code graph | Which shared code (`brownfield.layout.common_root`) links services? | `graphify-out/graph.json` | `graphify affected <SharedClient>` (unique label) |
| Service graph | Which other services call or subscribe to it? | `graphs/service-graph.json` (services.yaml, OpenAPI or code routes, events.yaml, REST clients / publishers / handlers found by the convention presets, traces) | `tools/context/service_graph.py`; presets: `tools/context/conventions.py` |
| Quality / test graph | Which tests execute the affected lines? | `var/quality/<svc>-coverage.json` (coverage.py / JaCoCo / lcov / Cobertura / Go / Istanbul; per-test where recorded) | `scripts/run_tests.py <svc>` |
| QA test cases | Which manual / BDD test cases cover it? | `brownfield.test_cases` (Zephyr / Xray JSON, Gherkin, CSV; `Covers` field or endpoints in steps) | manifest `tests.test_cases`; `tools/context/test_cases.py --covers <symbol>` |
| Knowledge | Which rules/ADRs/runbooks govern it? | `docs/**`, `README.md`, `contracts/events.yaml` | manifest `knowledge` |
| Configuration | Which flags, env vars, routes apply? | `config/services.yaml`, application config, optional `config/flags.json` / `config/subscriptions.yaml` | manifest `config` |
| Git / history | How often and how recently did it change? | `git log` | manifest `history` |
| Runtime | Is the dependency real in traffic? | `var/traces/*.jsonl` | service graph `runtime` |
| Memory | What happened last time we touched it? | `artifacts/memory/episodes.jsonl` | manifest `memory` |
| Knowledge base | What do policies, specs and spreadsheets say about it? | `knowledge/**` (pdf, xlsx, csv, md, txt) → `graphs/kb/` (own FAISS + BM25 index, separate from the code index) | manifest `knowledge.documents`; `tools/context/knowledge_base.py search "…"` (cite `KB:<source>#<locator>`; context, never scope) |
| Semantic index | Where does a task in *business* wording land? | `graphs/semantic/` (FAISS + BM25 over enriched nodes, rules, APIs, topics, docs) | `tools/context/semantic_index.py search "…" --expand "…" --seeds` |

Code nodes in every `graph.json` are enriched by `tools/context/enrich_graph.py` with `signature`, `docstring`,
`fields`, `route`, `publishes`/`handles`, `business_rules`, `tests`, `line_coverage`, `summary` — read them before
opening the file.

## Phases

1. **Intake.** Save the task verbatim under a `## Task text` heading in `artifacts/changes/<task-id>/task.md`
   (classification goes under `## Intake classification`; `--task-file` reads only the task-text section). Run
   `python scripts/intake-safety-scan.py artifacts/changes/<task-id>` (rule 31). Task id: ticket id if given, else
   `CR-<YYYYMMDD>-<slug>`.
2. **Freshness.** `python tools/context/refresh.py --check` — every service, not only the primary (the manifest reads
   impacted services' graphs, but records freshness for the primary only). It compares content hashes of the source
   files and of the non-code inputs enrichment used (business rules, coverage, published topics), the service-graph
   input digest, the semantic corpus vs the index, and `knowledge/` vs the knowledge base. Exit 2 → `/refresh-context`
   (`refresh.py --stale`: graphify only where code changed, enrichment only where rules/coverage changed, only
   changed documents re-embedded; add `--tests` when coverage is missing). Exit 3 = a refresh is running: wait.
   Exit 1 = a stage failed: STOP and report it. Nothing refreshes on its own (hooks do not run in Claude Code), so
   check even when you changed nothing yourself.
3. **Discovery run.** Write 1–3 **query expansions**: the task restated in the system's own vocabulary (entity,
   operation, rule and event words from `GRAPH_REPORT.md` community names, `docs/business-rules.md`,
   `graphs/SERVICE_GRAPH.md`) — e.g. "prevent overselling" → `--expand "reserve stock for an order all-or-nothing"
   --expand "insufficient stock rejects the order"`. Expansions must restate the task, never add scope. Then run
   `python tools/context/manifest.py --task-file artifacts/changes/<id>/task.md --id <id> --expand "…" [--expand "…"]`.
   Read `impact-analysis.md` → *Seeds* and *semantic candidates* (score + the rule/API/topic/code hit that led there).
   `seeds.source: semantic` means no name matched: treat every landing point as a hypothesis until you read it.
   Semantic search is **required** (`brownfield.semantic.required`): every run, including the final `--seed` run,
   searches FAISS + BM25 and the knowledge base and records `seeds.semantic_search.ran: true`. Exit 5 means the
   packages or the index are missing: STOP, `python scripts/setup_toolchain.py --check` for the same `python` (repair
   without `--check`), then
   `refresh.py --stale`. Do not switch interpreter or pass `--semantic off` (refused).
4. **Seed refinement (the judgement step).** Read the seed symbols' source. Decide the true landing points:
   - drop noise seeds (a word matched a name by accident);
   - add missed ones: `--seed domain.update_order` / `--seed OrderServiceImpl.approve` (module or class + member),
     `--seed discount_cents` / `--seed rejectionReason` (field), `--seed ORDER_STATUS_APPROVED` (enum constant),
     `--seed order.updated` (topic), `--seed billing:domain.create_invoice` (other service); promote good *semantic
     candidates* and `seeds.candidate_fields` the same way. In camelCase code a one-word field the task mentions
     (`status`, `type`) is only a candidate: confirm it with `--seed` when it is really meant;
   - inspect a symbol with its **graph node id** from the manifest (`dependencies.direct[].graph_node`), e.g.
     `graphify explain orders_service_domain_update_order --graph services/orders/graphify-out/graph.json` and
     `graphify affected orders_service_domain_update_order --graph … --depth 2`. Labels such as `update_order()`
     are ambiguous (api + domain) and `module.function` is not a graphify name — use ids. `graphify query` is keyword
     BFS and noisy; treat its output as leads only. Set `PYTHONIOENCODING=utf-8` on Windows.
   - **New concepts** (a field/endpoint that does not exist yet): do not seed them — they are reported under
     `seeds.unresolved` from the task text. Seed where they will live (the entity model + its schemas, the function
     that must enforce them).
   - **Several services must change:** seed each (`--seed shipping:domain.schedule_shipment`); they appear in
     `services.must_change` and `dependencies.must_change_services` (rule 40.10).
   A field seed means *code that reads/writes the field* (getters / setters / record accessors count as the field);
   also seed the declaring class (`--seed schemas.OrderOut`, `--seed ApprovalRequest`) when the field's shape
   changes (add/rename/retype/remove). A business-rule id in the task (`BR-06`) seeds the symbols its rules table cites.
   - **QA test cases** (`tests.test_cases`): `direct` cases cover a changed symbol, endpoint or field: list in the
     change plan which assertions change and which new cases the new behaviour needs (judgement, not tool output);
     `transitive` cases are the regression set. Cases without a `Covers` field are matched only by endpoints in
     their steps: say so when the list looks short.
   Re-run with `--seed …` (explicit seeds replace heuristic ones). Max 3 refinement iterations; record each seed
   decision with a one-line reason in the ledger.
5. **Judgement pass.** Add to the manifest under `unknowns` / `conflicts` (never delete generated entries):
   - behaviour the task implies but no source defines (rule 22 → `ASSUMPTION-<id>`);
   - doc vs code disagreements you found while reading (e.g. README says 3 retries, code retries 1);
   - additive vs breaking: a new optional response field is additive; renaming/removing/changing type is breaking.
   Record the outcome of risk-workflow-selector in `builder_notes.final_workflow` (the only override field;
   the effective workflow is the stricter of it and `workflow.selected`, rule 40.3). Plan status follows rule 40.9:
   `Ready` (nothing pending), `Pending Approval` (assumptions for the human), `Clarify` (blocking unknowns).
6. **Plan.** Write `change-plan.md` from `.claude/templates/change-plan-template.md`: steps per file, tests to add
   first (characterisation tests for uncovered symbols), consumer checks, rollout/migration notes, gates.

## Confidence rubric (computed by the tool)

| Component | Weight | 1.0 means |
|---|---|---|
| intent_resolution | 0.25 | every task term maps to code (explicit seeds all resolved) |
| graph_freshness | 0.10 | code graph built from the current source and enrichment inputs (content hashes, committed or not) |
| test_evidence | 0.20 | seed symbols fully executed by tests |
| dependency_clarity | 0.15 | every cross-service edge confirmed by static + contract + runtime, no graph conflicts |
| knowledge_grounding | 0.10 | a business rule governs the area |
| unknowns | 0.20 | no unknowns (blocking = −1.0, major = −0.2, minor = −0.05) |

Any `blocking` unknown caps overall at 0.40.

## Risk score (computed by the tool)

public schema touched +2 · each other must-change service +2 · each impacted (read-only) service +1 (max 2) ·
event with subscribers +2 · persistence model +2 (+1 without migrations) · no coverage +2 / weak coverage +1 ·
business rule +1 · feature flag +1 · endpoint behaviour only +1. Bands from `brownfield.risk_levels` in
`.claude/config.yaml`.

## Must NOT

- Hand-write graph facts, or edit generated sections of `context-manifest.yaml` other than appending to
  `unknowns`, `conflicts`, and the `builder_notes` block (schema: `.claude/templates/context-manifest-template.yaml`).
- Lower `risk` or raise `confidence` (rule 40). Escalate via `decisions.md` waiver only.
- Write product code — that is change-agent in `/implement-change`.
