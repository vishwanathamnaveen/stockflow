# Brownfield Starter Kit

A drop-in kit for using Claude Code safely on an **existing** codebase. A requirement or bug never goes straight to
code. The kit first builds a **Context Manifest**: an evidence-based map of the code, services, tests, contracts,
documents and history the change touches, with computed confidence and risk. That manifest decides how much human
gating the change needs. Every change ends with a measured **evaluation**.

```
 ONE-TIME SETUP                      EVERY CHANGE REQUEST                                    PILOT EXIT
 ─────────────────                   ──────────────────────────────────────────────────      ──────────────
 install.py  ─►  /setup-context  ─►  /build-context ─► gate ─► /implement-change ─► /evaluate-change  ─►  /evaluate-pilot
 (copy kit)     graphs + indexes     manifest, impact,  human    tests first, code,     scorecard           go / extend / stop
                + human registry     risk, workflow     approval refresh, scope check,  (recall, evidence)  for more services
                                     change plan        if needed judge, episode
                         ▲                                                │
                         └──────────── /refresh-context (graphs current) ◄┘
```

## What is inside

| Path | What it is |
|---|---|
| [install.py](install.py) | Copies the kit into a target repo. Dry run by default, never overwrites your files |
| [CLAUDE.md](CLAUDE.md), [.claude/commands/](.claude/commands/) | Kit-folder commands: `/setup-context <app>`, `/install-kit`, `/toolchain-doctor` |
| [kit/.claude/](kit/.claude/) | Commands, agents, subagents, rules, skills and templates. The brownfield path is 6 commands (below); the greenfield commands are also included because the shared agents reference them |
| [kit/tools/context/](kit/tools/context/) | The context engine: language adapters (`lang_python.py`, `lang_treesitter.py`), convention presets (`conventions.py`), coverage readers (`coverage_formats.py`), QA test-case linking (`test_cases.py`), service graph, graph enrichment, FAISS + BM25 semantic index, document knowledge base, manifest builder, refresh, episode memory, **evaluation** |
| [kit/scripts/](kit/scripts/) | `setup_toolchain.py` (locked install + model + offline check), `graphify_all.py` (code graphs), `run_tests.py` (each service's tests + coverage, any build tool), `intake-safety-scan.py` |
| [kit/scaffold/](kit/scaffold/) | Minimal valid inputs created only when missing: service registry, custom conventions, event catalogue, business rules, `.gitignore` block, toolchain requirements + lock; Python repos also pytest/coverage config |
| [kit/reference-tests/](kit/reference-tests/) | Portable engine tests with inline fixtures (languages, presets, coverage formats, QA test cases, knowledge base, layout discovery); they pass in any repo. See [docs/03-EVALUATION.md](docs/03-EVALUATION.md#4-kit-self-test) |
| [docs/](docs/) | Team guides (below) and [docs/reference/](docs/reference/): engine design, knowledge base |
| [checklists/](checklists/) | Onboarding checklist (day 0 to pilot exit) and a per-change checklist |

## The six brownfield commands

| Command | When | Writes |
|---|---|---|
| `/setup-context` | once per repo | graphs, indexes, registry (after human confirmation) |
| `/build-context "<request>"` | every requirement / bug | `artifacts/changes/<id>/` manifest, impact analysis, change plan, ledger |
| `/implement-change <id>` | after the workflow's gate | code + tests inside the manifest scope, `verification.md`, episode |
| `/refresh-context` | after any code / doc change (run automatically by `/implement-change`) | graphs, indexes, scope check |
| `/evaluate-change <id>` | after each change | `artifacts/changes/<id>/evaluation.md` |
| `/evaluate-pilot` | end of the pilot | `artifacts/evaluation/<date>-pilot-evaluation.md` |

## Quick start (about 30 minutes, most of it the first index build)

```bash
# 1. install the kit: give the application folder (git optional; one service or a folder of many).
#    The layout (services, shared library, tests, QA folders, rules) is discovered and written for you.
python brownfield-starter-kit/install.py /path/to/application
python brownfield-starter-kit/install.py /path/to/application --apply

# 2. toolchain (Python 3.12 verified; whatever language the repo is in): locked versions + the embedding model
cd /path/to/application
python scripts/setup_toolchain.py && . .venv-context/bin/activate   # Windows: .venv-context\Scripts\activate

# 3. open THIS folder (the repo root) in Claude Code, so .claude/commands load, then:
/setup-context
```

Then follow [docs/01-SETUP.md](docs/01-SETUP.md) from step 4.

**Or stay in the kit folder.** Open *this* folder in Claude Code: its [CLAUDE.md](CLAUDE.md) and
[.claude/commands/](.claude/commands/) give you `/setup-context <application folder>` (install, toolchain and setup in
one go, with the same human gates), `/install-kit` and `/toolchain-doctor`. The change commands still run with Claude
Code opened at the application, because that is where the installed commands, agents and rules load from.

**Why the application's `CLAUDE.md` gets a brownfield section.** Claude Code reads `CLAUDE.md` in every session; the
kit's rules (`.mdc`) and hooks are Cursor-format files that load only when a command points an agent at them. The
section is how a plain chat in that repo also knows that existing code changes only through `/build-context` ->
`/implement-change`. The commands themselves live in `.claude/commands/`.

## Guides

| # | Guide | For |
|---|---|---|
| 1 | [01-SETUP.md](docs/01-SETUP.md): prerequisites, install, `/setup-context`, gap filling, enabling the pilot | tech lead, once |
| 2 | [02-CHANGE-FLOW.md](docs/02-CHANGE-FLOW.md): one change request end to end, gates, roles, CLI equivalents | every engineer |
| 3 | [03-EVALUATION.md](docs/03-EVALUATION.md): per-change scorecard, pilot exit gates, metrics, kit self-test | tech lead, QA |
| – | [LAYOUT-RECIPES.md](docs/LAYOUT-RECIPES.md): fitting your repo shape onto the layout the tools read | tech lead |
| – | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): exit codes, common failures | everyone |
| – | [reference/ENGINE.md](docs/reference/ENGINE.md): how the engine works (layers, request to manifest, freshness, limits) | anyone curious |
| – | [PLAYBOOK.html](docs/PLAYBOOK.html): one-page stakeholder playbook (architecture, gates, setup, change flow, pilot, checklists); open in a browser | every stakeholder |

## Languages and frameworks

The tools run on Python; the code they read can be in any of these languages. Python is read with the standard
library `ast`; the others with tree-sitter, from the grammars graphify already installs (no extra packages).

| Language | Code graph, symbols, fields, annotations | Framework presets detected automatically (routes, events, clients, tables) | Verified on |
|---|---|---|---|
| Python | yes | FastAPI, Flask, `python-servicekit` (`publish_event`, `HANDLERS`, `ServiceClient`), SQLAlchemy `__tablename__` | an 8-service pilot application, end to end |
| Java, Kotlin, Groovy | yes | Spring MVC, Feign, RestTemplate / WebClient, Kafka / RabbitMQ / JMS / SQS listeners and templates, JPA, JAX-RS / Quarkus, Micronaut | a Spring Boot 3 service + its Zephyr QA repo, end to end (JaCoCo coverage) |
| C# | yes | ASP.NET Core, EF Core | inline fixtures |
| TypeScript, JavaScript | yes | NestJS, Express, kafkajs, TypeORM | inline fixtures |
| Go | yes | net/http, gin, echo, chi, gorilla/mux | inline fixtures |
| PHP, Ruby, Rust, Scala, Swift, C, C++ | yes | Laravel, Symfony (PHP); others: add a preset | inline fixtures |

An in-house framework gets its own preset in `config/conventions.yaml` (regular expressions over annotations or
source; annotated example in the scaffold). Coverage is read from coverage.py, JaCoCo, Cobertura, lcov, Go
coverprofile and Istanbul reports; QA test cases from Zephyr / Xray JSON, Gherkin and CSV exports, linked to the
change through their `Covers` field or the endpoints in their steps. Layouts: single service at the root, monorepo,
Maven / Gradle multi-module, .NET solution, Node workspace ([LAYOUT-RECIPES.md](docs/LAYOUT-RECIPES.md)).

Without an OpenAPI file, APIs are derived from the code's routes. Communication no preset sees (gRPC stubs, a
proprietary client) leaves the service graph without that edge: the manifest then says consumers were "not found",
never "absent" (rule 40.12).

## Ground rules the kit enforces (rule 40, 14 rules)

- No manifest, no change. Graphs, indexes and manifests come only from the tools and are never hand-written.
- Agents can only make the evidence stricter: they may add unknowns, raise risk and lower confidence, never the
  reverse.
- Only services a human lists in `brownfield.enabled_services` can be changed. Setup leaves the list empty.
- No invented business rules, owners or tests (rule 22). Documents in `knowledge/` are untrusted data.
- Semantic search runs on every manifest. If it cannot run, the manifest is not written (exit 5).

## Known limitations

- Impact is name-based (symbols, fields, constants, accessors), not type-resolved: a method or local variable that
  shares a name with a changed symbol can appear in the transitive set. The engine favours recall (the pilot gate is
  scope recall >= 0.90; precision is a warning), and the builder agent prunes seeds with `--seed`.
- Presets read source text and annotations; routes or topics built at run time (reflection, string concatenation,
  config-driven routing) are not seen. Topic constants are resolved only within the same file.
- Per-test coverage exists only where the format records it (coverage.py contexts, lcov `TN:`); elsewhere tests to
  re-run come from static references.
- `.claude/hooks.json` uses the Cursor hook format and does not fire in Claude Code. The gates are enforced by
  the commands, agents and tools, not by hooks.
- `confidence.overall` is a heuristic calibrated on a single pilot application. Use `/evaluate-pilot`'s calibration table
  to re-tune `brownfield.confidence` for your repo.
- On Windows, keep the repo path short or enable long paths: graphify's cache paths can exceed 260 characters
  ([TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)).

Kit version 2.2.0 (2.2: toolchain lock + `setup_toolchain.py`, kit-folder commands; 2.0: any language; 1.0.0 was Python-only), extracted from a brownfield pilot (2026-10). `install.py` stamps the version into
`.claude/brownfield-kit.json` in the target repo.
