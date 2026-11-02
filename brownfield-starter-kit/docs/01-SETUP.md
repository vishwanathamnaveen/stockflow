# 1. Setup: from an empty repo to the first change request

Owner: tech lead. Time: about half a day, including the human decisions. Do it once per repository.

## 0. Prerequisites

| Need | Why | Check |
|---|---|---|
| Python ≥ 3.10 | every tool (the code itself can be Java, C#, TypeScript, Go, ... see [LAYOUT-RECIPES.md](LAYOUT-RECIPES.md)) | `python --version` |
| the service's own build tool (Maven, Gradle, dotnet, npm, go, pytest) | tests + coverage (`test_command`) | it runs from the same shell |
| git (optional) | change history and commit stamps in manifests; without it freshness still works (content hashes) and the files a change touched come from a content snapshot | `git rev-parse HEAD` |
| Claude Code, opened at the **repo root** | `.claude/commands` load only from the folder you open | `/setup-context` appears in the command list |
| ~2 GB disk, CPU only | torch (CPU), sentence-transformers, FAISS | no GPU needed |
| Internet once (or a proxy / pre-seeded HF cache) | the embedding model `BAAI/bge-small-en-v1.5` downloads on the first index build | after that nothing leaves the machine |
| Windows: a short repo path, or long paths enabled | graphify cache paths can exceed 260 characters | see [TROUBLESHOOTING.md](TROUBLESHOOTING.md#windows-path-too-long) |

Decide up front: **which service is the pilot** (one service with decent tests and an owner who will review), and
**who owns each service** (the owner gate forces `guarded` for services without an owner).

## 1. Install the kit

```bash
python brownfield-starter-kit/install.py /path/to/application            # dry run: discovered layout + file list
python brownfield-starter-kit/install.py /path/to/application --apply
```

The path is the application folder: one service, a monorepo, or a folder holding several service folders, a shared
library and a QA test-case folder side by side. The installer discovers the layout from build files and folders
(`tools/context/discover.py`: Maven / Gradle modules, npm workspaces, .NET projects and their test projects, Go
modules, Python packages, shared libraries, QA folders, business-rule tables) and writes `config/services.yaml` and the
`brownfield:` layout. Only `owner` and `description` stay `TBD` for you. Re-plan any time with
`python tools/context/discover.py` (add `--write --force` to regenerate the registry).

What it does:

| Action | Files |
|---|---|
| copy (kit-owned) | `.claude/**`, `tools/context/**`, `scripts/{_paths,graphify_all,run_tests,intake-safety-scan}.py`, `tools/context/reference-tests/`, `docs/context-engine/starter-kit/` (these guides; excluded from the knowledge index) |
| copy only if missing | `config/services.yaml`, `config/conventions.yaml`, `contracts/events.yaml`, `docs/business-rules.md`, `.graphifyignore`, `knowledge/`; Python repos also `pytest.ini`, `.coveragerc` |
| copy (toolchain) | `tools/context/requirements.txt`, `tools/context/constraints.txt` (the lock), `scripts/setup_toolchain.py` |
| append missing lines | `.gitignore` (generated artifacts); Python repos: `requirements.txt` (toolchain block; your existing pins are kept and reported) |
| append a section | `CLAUDE.md` (the brownfield flow, so every session knows it) |
| stamp | `.claude/brownfield-kit.json` (kit version) |

It reports the languages and build tools it finds. It never overwrites an existing file. Kit files that already exist with other content are listed as
`keep (differs)`; review them, or rerun with `--upgrade` to take the kit's version. `.claude/config.yaml` is never
overwritten: if yours has no `brownfield:` block, copy it from `kit/.claude/config.yaml` (or let `/setup-context` do
it). The installer does not run git; a repository is optional.

## 2. Toolchain

```bash
cd /path/to/repo
python scripts/setup_toolchain.py                 # Windows with several Pythons: py -3.12 scripts/setup_toolchain.py
. .venv-context/bin/activate                      # Windows: .venv-context\Scripts\activate
python scripts/setup_toolchain.py --check         # any time later: verify only, installs nothing
```

The script creates `.venv-context` (Python repos: `--venv <the repo's .venv>`), installs torch from the CPU index,
then `tools/context/requirements.txt` with `tools/context/constraints.txt`, the exact version of every transitive
package verified together. That lock is what stops the usual breakage: a bare `pip install -r requirements.txt`
resolves new `transformers`, `huggingface_hub`, `tokenizers` or `numpy` releases on every machine. It then downloads
the embedding model once (through the OS certificate store, retrying without Xet) and proves everything offline.

No access to huggingface.co? One person who has the model runs `python scripts/setup_toolchain.py --export-model
bge.zip`; everyone else runs `python scripts/setup_toolchain.py --model-cache bge.zip`. Internal PyPI mirror: set
`PIP_INDEX_URL` and add `--torch-index default`. Problems: [TROUBLESHOOTING.md](TROUBLESHOOTING.md#toolchain-install).

Every later command, and every agent, must use this same `python`. The service's build tool (for `test_command`)
must work from the same shell; behind a TLS-inspecting proxy the JDK / npm / NuGet may need the company root CA (see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

## 3. Run `/setup-context`

Open the repo root in Claude Code and run the command below. (Opened at the starter kit folder instead?
`/setup-context /path/to/repo` there does steps 1 to 3 in one go; see the kit's `CLAUDE.md`.)

```
/setup-context                                   # discover services under brownfield.layout.services_root
/setup-context docs=/path/to/specs               # also index PDFs / Excel / CSV / notes into knowledge/
```

The context-bootstrap-agent does the following:

1. **Preflight** (read-only): kit files, Python, interpreter.
2. **Layout plan**: maps your repo onto the layout the tools read ([LAYOUT-RECIPES.md](LAYOUT-RECIPES.md)) and drafts
   `config/services.yaml` from disk.
3. **Gate 1, you**: confirm the service list, the source folders, each service's test command and coverage report
   (the agent proposes them from the build tool), where QA test cases live, and **one business-language description
   per service**.
   Descriptions feed the semantic index, so write them yourself; never let the agent guess them. Owners: real team
   names, or `TBD`. A `TBD` owner makes changes to that service `guarded`.
4. **Scaffold** missing inputs only, and set `brownfield.layout` and `enabled_services: []` in `.claude/config.yaml`.
5. **First build**, stopping at the first failure:

   | Stage | Command | Output |
   |---|---|---|
   | a | `python tools/context/service_graph.py` | `graphs/service-graph.json`, `SERVICE_GRAPH.md` |
   | b | `python scripts/run_tests.py` | `var/quality/<svc>-coverage.json` (each `test_command`; per-test where the format records it) |
   | c | `python scripts/graphify_all.py` | `<svc>/graphify-out/graph.json` (+ shared library, overall) |
   | d | `python tools/context/semantic_index.py build` | `graphs/semantic/` (FAISS + BM25) |
   | e | `python tools/context/knowledge_base.py build` | `graphs/kb/` (only if `knowledge/` has files) |
   | f | `python tools/context/refresh.py --stale` | `var/context/snapshot.json` |

   Failing test suites are **not fixed** by the agent. They are listed, and their services get
   `coverage: missing`, which lowers test-evidence confidence.
6. **Verify**: `refresh.py --check` exits 0, a smoke semantic search, and a smoke manifest in a scratch directory
   with `semantic_search.ran: true`.
7. **Audit**: `artifacts/audit/<date>-setup-context.md`.

Without Claude Code, you can run the same stages by hand in the order above. The agent adds the layout plan, gate 1
and the gap report.

## 4. Fill the gaps the report lists

Each gap lowers manifest confidence for the affected services. Close the ones on your pilot service first.

| Gap | Effect if left | Fix |
|---|---|---|
| no OpenAPI contract (`contracts/openapi/<svc>.json\|yaml`) | APIs come from the code's routes only; request / response shapes are read from signatures | export it from the framework (FastAPI `app.openapi()`, springdoc `/v3/api-docs`, Swashbuckle, `@nestjs/swagger`) |
| a framework without a preset (0 routes / handlers in `conventions.py`) | no API / event / client edges for that service | a preset in `config/conventions.yaml` ([LAYOUT-RECIPES.md](LAYOUT-RECIPES.md#i-a-framework-the-presets-do-not-know)) |
| coverage without per-test data (JaCoCo, Cobertura, Go) | tests to re-run come from static references | fine for a pilot; per-test needs lcov `TN:` or coverage.py contexts |
| QA test cases without a `Covers` field | linked only through endpoints in their steps | add traceability (endpoints, `Class.method`) in the test-management tool |
| empty `docs/business-rules.md` | manifests cannot link code to rules; rule-touching changes look riskier | add rules **a human confirms**, `\| BR-nnn \| rule \| <svc> \`symbol\` \|` |
| failing / missing test suites | `test_evidence` low, so no fast-track | fix the tests as normal work (through the change flow) |
| `TBD` owners | every change to that service is `guarded` | name an owner |
| unparsable `contracts/events.yaml` | every event-touching change is `clarify` | make it strict YAML (as a gated contract change) |
| no `knowledge/` documents | manifests carry no requirement / spec context | add specs with no personal data (see [reference/KNOWLEDGE-BASE.md](reference/KNOWLEDGE-BASE.md)) |

After filling gaps, run `/refresh-context` (or `python tools/context/refresh.py --stale`).

## 5. Enable the pilot service (human edit)

```yaml
# .claude/config.yaml
brownfield:
  enabled_services: [orders]        # only these can be changed by /implement-change
```

Every other service stays analyze-only. A change that must touch a disabled service gets the `analyze-only`
workflow. Split it, or enable that service too.

Optional, before the first change:

- `brownfield.external_catalog`: point it at a service catalog or API-gateway registry if consumers live outside
  this repo. Without one, consumers outside the repo are "not ruled out", never "proven absent".
- Commit the setup (`.claude/`, `tools/`, `scripts/`, `config/`, `**/graphify-out/graph.json`,
  `graphs/service-graph.json`), so the whole team and CI share the same graphs. Then add
  `python tools/context/refresh.py --check --committed-only` to CI.

## 6. First change request

```
/build-context "Reject orders whose total is above 1,000,000 cents"
```

Continue with [02-CHANGE-FLOW.md](02-CHANGE-FLOW.md). For a first run, choose a small, low-risk change on the pilot
service, so the team sees the whole loop (manifest, fast-track, tests first, scope check, evaluation) before
anything risky.

## Setup is done when

- [ ] `python tools/context/refresh.py --check` exits 0 (only listed coverage gaps)
- [ ] smoke manifest exit 0 with `seeds.semantic_search.ran: true`
- [ ] registry confirmed; owners and descriptions written by humans
- [ ] pilot service in `enabled_services`
- [ ] `artifacts/audit/<date>-setup-context.md` exists
- [ ] the team has read [02-CHANGE-FLOW.md](02-CHANGE-FLOW.md)
