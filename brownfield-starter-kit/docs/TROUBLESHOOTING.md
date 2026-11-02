# Troubleshooting

## Exit codes

| Tool | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `refresh.py --check` | fresh | a step failed | stale: run `--stale` | another refresh holds the lock: wait | | |
| `refresh.py --stale` | refreshed | a stage failed (see output) | | locked | | |
| `manifest.py` | manifest written / within scope | | bad arguments or input (message says why) | | `--verify-scope`: scope grew, so `--amend` | semantic stack / index missing: nothing written |
| `evaluate.py` | PASS | ATTENTION | FAIL | nothing to evaluate | | |

Never work around exit 5 (another interpreter, `--semantic off`) and never delete `var/context/refresh.lock` by hand.

## Common failures

| Symptom | Cause | Fix |
|---|---|---|
| `/setup-context` is not in the command list | Claude Code opened at a parent folder | open the repo root (the folder that holds `.claude/`) |
| `graphify is not installed` | different interpreter than the one you installed into | activate the venv; check with `python -c "import graphify"` |
| `KeyError: '<service>'` | registry name differs from the folder name, or `package` is wrong | fix `config/services.yaml` (re-confirm with the owner) |
| `set brownfield.layout.common_package` | `common_root` has 0 or several packages | set `common_package`, or `common_root: null` |
| graphify `FAIL ... extract` with `No such file or directory ... graphify-out\cache\...tmp` | Windows path over 260 characters | see below |
| `pytest: error ... -c` | `pytest.ini` / `.coveragerc` missing at the root (Python services) | rerun `install.py --apply` (it adds missing ones in Python repos) |
| `skipped: no test_command for <svc>` | a non-Python service has no declared test command | add `test_command` + `coverage` to `config/services.yaml` (the message suggests one) |
| `no coverage report written by this run` | wrong `coverage.path`, the coverage plugin did not run, or the tests failed before the report | fix the path / command; a report from an earlier run is never reused |
| coverage meta lists `unmatched` report paths | report paths do not end in the service's source paths | check `path` / `package`; exclude generated sources |
| Maven / Gradle `PKIX path building failed`, npm `UNABLE_TO_GET_ISSUER_CERT` | TLS-inspecting corporate proxy: the toolchain lacks the company root CA | use the team's truststore (`MAVEN_OPTS=-Djavax.net.ssl.trustStore=<file>`, `NODE_EXTRA_CA_CERTS`) or the internal mirror; never disable certificate checks |
| `conventions.py` shows 0 routes for a service with endpoints | its framework has no preset | write one in `config/conventions.yaml` ([LAYOUT-RECIPES.md](LAYOUT-RECIPES.md#i-a-framework-the-presets-do-not-know)) |
| `unknown convention preset` | a name in `conventions:` is neither built-in nor in `config/conventions.yaml` | `python tools/context/conventions.py --list` |
| a class is treated as a test | a `brownfield.tests.patterns` glob matches it (matching is case-sensitive on every OS) | narrow the pattern |
| QA test cases missing from manifests | `brownfield.test_cases` path wrong, or cases have no `Covers` field and no endpoints in their steps | `python tools/context/test_cases.py` shows what loads |
| `ModuleNotFoundError` for the service package in `run_tests.py` | package not importable from the service folder | check `package:`; for `src/` layouts use `package: src/<pkg>` ([LAYOUT-RECIPES.md](LAYOUT-RECIPES.md)) |
| `coverage: missing` in `--check` | the suite failed or has no tests | fix tests through the change flow; until then that service cannot fast-track |
| `semantic-index unavailable` / manifest exit 5 | faiss / sentence-transformers not in this `python`, or no index | `python scripts/setup_toolchain.py --check` (repair without `--check`); `semantic_index.py build` |
| model download fails | proxy / offline | see [Toolchain install](#toolchain-install) |
| `--verify-scope`: `manifest records no explicit_seeds` | manifest built from lexical seeds only | rerun `/build-context` and confirm the seeds (`--seed svc:symbol`) |
| every manifest is `analyze-only` | service not in `brownfield.enabled_services` | a human enables it (setup step 5) |
| every event-touching manifest is `clarify` | `contracts/events.yaml` is not strict YAML | fix the catalogue (as a gated contract change) |
| manifest finds no symbols, `clarify` | the request uses words the code does not, or the files are in a language no adapter reads | add `seed=`; write service descriptions and business rules; `conventions.py` lists languages per service |
| `evaluate.py` reports `__pycache__` / `.pyc` as unpredicted | `.gitignore` lacks them and the files are tracked | `git rm -r --cached '**/__pycache__'`; the installer's `.gitignore` block ignores them |
| knowledge base passages "excluded" | ID- / card-shaped values or injection-like text | redact the source document; the excluded text is never printed |

## Toolchain install

Always install with `python scripts/setup_toolchain.py` and diagnose with `--check`; from the starter kit folder,
`/toolchain-doctor <repo>` does the same. The script names the failing step and its fix.

| Symptom | Cause | Fix |
|---|---|---|
| `No matching distribution found for torch==...` / `faiss-cpu==...` | Python version without wheels (often a brand-new Python) | recreate the venv with 3.12: delete `.venv-context`, `py -3.12 scripts/setup_toolchain.py` |
| `ImportError` / `AttributeError` inside `transformers`, `huggingface_hub`, `tokenizers` or numpy | transitive versions drifted (a bare `pip install -r`, or a hand upgrade) | `python scripts/setup_toolchain.py` (reinstalls from the lock); `--check` lists the drift |
| pip `ResolutionImpossible` in a Python repo | a repo pin disagrees with `tools/context/constraints.txt` | align that pin as a normal change, or ask the kit owner to re-verify the lock; never `--no-lock` |
| torch download of several GB (`nvidia-*` packages) | torch came from PyPI on Linux (CUDA build) | the script installs it from the CPU index; behind a mirror use `--torch-index <mirror>/whl/cpu` |
| `download.pytorch.org` blocked | corporate firewall | `--torch-index default` with `PIP_INDEX_URL` set to the internal mirror |
| `SSL: CERTIFICATE_VERIFY_FAILED` from pip or Hugging Face | TLS-inspecting proxy | pip >= 24.2 and the script's model download use the OS certificate store (`truststore`); make sure the company root CA is in it. Never `--trusted-host` or disabled verification |
| `huggingface.co` unreachable, `LocalEntryNotFoundError`, `OfflineModeIsEnabled` | no internet / proxy | `HTTPS_PROXY=<proxy>`, or `HF_ENDPOINT=<internal mirror>`, or a teammate's export: `--export-model bge.zip` on theirs, `--model-cache bge.zip` here |
| download stalls or fails in `hf_xet` | proxy breaks the Xet transfer protocol | the script retries with `HF_HUB_DISABLE_XET=1`; set it yourself for manual downloads |
| `401` / `429` from Hugging Face | rate limit on anonymous downloads behind a shared office IP | retry later, or use a teammate's export |
| works in your shell, fails in Claude Code or CI | a different `python` | activate `.venv-context` before starting Claude Code; CI runs `setup_toolchain.py`, then the tools with the venv's python |

## Windows: path too long

graphify writes cache files such as
`<repo>\<services_root>\<svc>\graphify-out\cache\ast\v0.9.70-s4\<64-char hash>.<random>.tmp`, which adds about 120
characters to the repo path. Keep the repo path under ~130 characters (for example `C:\src\<repo>`), or enable long
paths (admin, then reboot or sign in again):

```powershell
New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
git config --global core.longpaths true
```

## Line endings

Hashes fold CRLF to LF, so a Windows checkout (`core.autocrlf=true`) and a Linux CI checkout of the same commit agree
on freshness. graphify's own `manifest.json` hashes raw bytes and is not portable, but nothing in the kit reads it.
