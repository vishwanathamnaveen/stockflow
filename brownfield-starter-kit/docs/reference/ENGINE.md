# The context engine: how a request becomes a Context Manifest

How the brownfield agents learn what a change will touch **before** they write code: how the system intelligence is
built, what happens when someone asks for a Context Manifest, and how it stays current when code changes. Examples
use placeholder names (`<service>`, `orders`); substitute your own.

## 1. The idea

An agent can edit a function in minutes. What it cannot see from the file is which other services call that code,
which events carry its fields, which business rules it implements and which tests prove all of it still works. The
context engine turns the repository into queryable graphs once, then answers "what does this task touch?" in
seconds and writes the answer to a file, the **Context Manifest**, that the code-change agent must obey.

Three rules make it trustworthy:

1. **Tools produce facts, agents add judgement.** Files, symbols, consumers, tests and scores are computed by
   deterministic scripts in `tools/context/`. Agents may only append unknowns, conflicts and notes, raise risk or
   lower confidence, never the reverse (rule 40).
2. **Everything is a file in the repo.** Graphs are JSON, the manifest is YAML, the index is a local FAISS file. No
   server, no database, no code leaves the machine (the embedding model downloads once).
3. **Freshness is checked, not assumed.** Every artifact records content hashes of its inputs, the engine version
   and a build-config hash; stale graphs stop `/build-context` and `/implement-change`.

```
 sources                      1. system intelligence              2. per request           3. agents
 ─────────────────────        ──────────────────────────          ─────────────            ─────────────────────
 service code          ──►    code graph (graphify + enrich)  ─┐
 contracts, config     ──►    service graph                   ─┤
 tests + coverage      ──►    quality graph                   ─┼──► manifest.py  ──►  context-builder-agent
 docs, rules, knowledge──►    semantic index, knowledge base  ─┤    (facts, scores,     (seeds, impact check,
 git, traces, episodes ──────────────────────────────────────── ┘     workflow)          plan) ──► change-agent
                                     ▲                                                              │
                                     └──────────── refresh.py, record_episode.py ◄──────────────────┘
```

## 2. Building system intelligence

Built once by `/setup-context`, then incrementally by `/refresh-context` (`python tools/context/refresh.py --stale`).

| Layer | Tool | Output | Answers |
|---|---|---|---|
| Code graph | graphify (tree-sitter, local, no LLM) via `scripts/graphify_all.py` | `<service>/graphify-out/graph.json` | what calls, uses or inherits what inside a service |
| Enrichment | `tools/context/enrich_graph.py` (inside `graphify_all.py`) | the same `graph.json`, extra fields per node | what each symbol *is*: signature, line range, route, published events, business rules, covering tests |
| Service graph | `tools/context/service_graph.py` | `graphs/service-graph.json`, `graphs/SERVICE_GRAPH.md` | which services call or subscribe to which |
| Quality graph | `scripts/run_tests.py` (each service's own build tool) | `var/quality/<service>-coverage.json` | which tests execute which lines |
| Semantic index | `tools/context/semantic_index.py build` | `graphs/semantic/` (local, git-ignored) | where a request in *business* words lands in code |
| Knowledge base | `tools/context/knowledge_base.py build` | `graphs/kb/` | which documents in `knowledge/` give requirement or spec context |

**Code graph and enrichment.** graphify stores per node only an id, label, file, start line and community: no
signature, end line, body or embedding. `enrich_graph.py` writes the missing facts into the same file (graphify
ignores extra keys, so `graphify explain / affected / query` keep working). Python is read with the standard library
`ast`; other languages with tree-sitter (`lang_python.py`, `lang_treesitter.py`).

**Service graph.** Services talk over HTTP and event buses, so no import edge links them. `service_graph.py`
rebuilds those links and records which evidence confirms each edge:

| Evidence | Source |
|---|---|
| `config` | `config/services.yaml`; optional broker-routing file `config/subscriptions.yaml` |
| `contract` | `contracts/openapi/<service>.json\|yaml`, `contracts/events.yaml` |
| `static` | REST clients, publishers and handlers found by convention presets (`conventions.py`: Spring / Feign, FastAPI, NestJS, ASP.NET Core, gin, ...; in-house frameworks in `config/conventions.yaml`) |
| `runtime` | client / consumer spans in `var/traces/*.jsonl`, when traces exist |

It also cross-checks the sources: an `events.yaml` that does not parse, a topic published in code but missing from
the catalogue, a topic routed to a service that has no handler for it.

**Semantic index.** Name matching fails when the request uses words the code does not. The index holds enriched
code nodes, business rules, API operations, event topics, doc sections and the service descriptions, each linked to
the code that implements it. Model `BAAI/bge-small-en-v1.5` (384 dimensions, CPU); FAISS exact cosine search plus
BM25, fused by reciprocal rank. Vectors are reused by text hash, so one changed function re-embeds one document.

## 3. From request to Context Manifest

| # | Step | Done by | Result |
|---|---|---|---|
| 1 | Intake: safety scan, type, id | task-intake-classifier | `task.md` |
| 2 | Freshness: `refresh.py --check` on every service | tool | stale graphs refreshed first |
| 3 | Discovery: lexical + semantic seeds, graph expansion | `manifest.py` | first `context-manifest.yaml` |
| 4 | Seed refinement: read the code, confirm landing points with `--seed <service>:<symbol>` (max 3 runs) | context-manifest-builder | refined manifest with `explicit_seeds` |
| 5 | Impact: direct, transitive, cross-service, runtime, data, regression, consumer effect per edge | impact-analyzer | `impact-analysis.md` |
| 6 | Confidence and risk computed; workflow selected; escalation only, never relaxation | `manifest.py`, risk-workflow-selector | `workflow`, `builder_notes` |
| 7 | Plan and decision ledger | context-builder-agent | `change-plan.md`, `decision-ledger.md` |

**Confidence** has six components (intent resolution, graph freshness, test evidence, dependency clarity, knowledge
grounding, unknowns) and a weighted overall. It is a heuristic, not a probability: decide on the components. A
critical gap (intent < 0.5, test evidence < 0.4, dependency clarity < 0.5) caps overall at 0.60.

**Risk** is additive (public contracts, dependent services, events with subscribers, business rules, persistence,
security-sensitive code) with bands in `brownfield.risk_levels`. **Mandatory gates** set floors no score can buy past.
The workflow table and gates are in rule 40 and [02-CHANGE-FLOW.md](../02-CHANGE-FLOW.md).

### Manifest anatomy

| Section | Source | Used by |
|---|---|---|
| `task`, `intake` | request text | everyone |
| `services`, `files`, `symbols`, `apis` | code graph + service graph | change-agent scope (the blast radius) |
| `dependencies` (direct, transitive, cross-service, identifier references) | code graph edges, service graph, field search | impact review, owner sign-off |
| `events`, `data` (incl. lineage) | service graph, models, OpenAPI, `events.yaml` | contract and migration gates |
| `rollout` | must-change services ordered provider before consumer | multi-service changes |
| `tests` | per-test coverage, static references, QA test cases | regression set, behavioural targets |
| `knowledge`, `config`, `history`, `runtime_evidence`, `memory` | rules, documents, config, git, traces, episodes | judgement |
| `retrieval` | every semantic and knowledge-base query and hit, with scores | reviewing seeds, tuning floors |
| `unknowns`, `conflicts` | tool + agents (append-only) | plan status |
| `confidence`, `risk`, `workflow` | computed | gates |
| `builder_notes` | agents only | seed decisions, escalations |

Schema with placeholder values: `.claude/templates/context-manifest-template.yaml`.

### Automatic versus judgement

| Automatic (tools, reproducible) | Judgement (agents, append-only, reviewed) |
|---|---|
| graphs, enrichment, indexes | choosing and dropping seeds |
| impact dimensions, regression set | restating the request for search (`--expand`) |
| confidence, risk, workflow | consumer effect: breaks / behaviour change / none |
| freshness, conflicts between sources | new unknowns, doc-versus-code conflicts, escalation |

## 4. Keeping it current

| Artifact | Stale when | Detected by | Rebuilt by `refresh.py --stale` |
|---|---|---|---|
| Code graph | a source file is modified, added or deleted, or the engine version / build config changed | line-ending-normalised content hash per file | graphify + enrichment |
| Enrichment facts | a cited business rule, coverage or a publish edge changes | input digests | enrichment only |
| Service graph | clients, handlers, publishers, contracts or config change | `inputs_digest` | `service_graph.py` |
| Semantic index | the corpus it would build now differs, or the model changed | content of the corpus, not file times | changed documents re-embedded |
| Quality graph | code or tests change | `--check` reports missing coverage | `--tests` re-runs the suites |
| A written manifest | its files changed after it was built | change-agent refuses; rebuild with `/build-context` | — |
| An implemented change | it reaches files, services, consumers or gates the manifest did not | `manifest.py --verify-scope <id>` (exit 4) | scope-change request (`--amend`) |

Refresh guarantees: one writer at a time (`var/context/refresh.lock`, exit 3 while held), stages in dependency order
stopping at the first failure, inputs digested before and after (a refresh whose inputs moved is retried once, then
fails), index files replaced atomically. Without git, artifacts record a content snapshot instead of a commit.

| Trigger | What runs |
|---|---|
| before every `/build-context` | `refresh.py --check`; `--stale` when exit 2 |
| after the last edit of `/implement-change` | `/refresh-context <id> --tests` + `manifest.py --verify-scope` |
| close of `/implement-change` | `refresh.py --check` must exit 0 |
| after pulls / branch switches outside the agents | `/refresh-context` (or a git hook, a team decision) |
| CI on push / PR | `refresh.py --check --committed-only` once graph JSON is committed |

## 5. Limits, and how they are guarded

| Limit | Guard |
|---|---|
| Impact is name-based, not type-resolved: unrelated symbols sharing a name can appear | the engine favours recall (pilot gate: scope recall ≥ 0.90); the builder prunes seeds |
| Routes or topics built at run time (reflection, string concatenation, config-driven routing) are not seen | consumers are "not found", never "proven absent" (rule 40.12); owners confirm before breaking changes |
| Per-test coverage only where the format records it | otherwise tests are selected from static references |
| Confidence weights are a starting point | `/evaluate-pilot`'s calibration table; thresholds re-tuned as a dated human decision |
| Documents may hold instructions or personal data | `knowledge_base.py` quarantines injection-shaped and sensitive passages; passages inform judgement, never scope |
