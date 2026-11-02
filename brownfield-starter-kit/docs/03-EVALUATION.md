# 3. Evaluation: did the brownfield path work?

Evaluation happens at four levels. The first three are deterministic (`tools/context/evaluate.py`, the tests) and the
fourth is a human decision based on their numbers.

| Level | When | How | Output |
|---|---|---|---|
| 1. Setup | end of `/setup-context` | `refresh.py --check`, smoke search, smoke manifest | setup audit |
| 2. Each change | after `/implement-change` (or a closed `clarify`) | `/evaluate-change <id>` | `artifacts/changes/<id>/evaluation.md` |
| 3. The pilot | after ≥ 5 recorded changes, or at the end of the pilot window | `/evaluate-pilot` | `artifacts/evaluation/<date>-pilot-evaluation.md` + GO / EXTEND / STOP |
| 4. The kit itself | after upgrading the kit or editing `tools/context/` | reference tests + sample repo smoke | test report |

## 1. Setup evaluation

| Check | Pass |
|---|---|
| `python tools/context/refresh.py --check` | exit 0; only coverage gaps the setup report already lists |
| `python tools/context/semantic_index.py search "<a service description in business words>" -k 3` | the right service in the top 3 |
| smoke `manifest.py ... --mode analyze --out <scratch>` | exit 0, `seeds.semantic_search.ran: true` |
| `knowledge_base.py status` (when documents exist) | `fresh`, excluded passages reported by location only |

## 2. Per-change scorecard: `evaluate.py change <id>`

What it checks:

| Check | Severity if it fails |
|---|---|
| `task.md`, `context-manifest.yaml`, `impact-analysis.md`, `change-plan.md`, `decision-ledger.md` exist | FAIL |
| semantic search ran for the manifest | FAIL (WARN for manifests older than the semantic gate) |
| fast-track despite `confidence.critical_gaps` | FAIL |
| executed workflows: `verification.md` exists | FAIL if the outcome was success, else WARN |
| an episode is recorded | WARN |
| files changed outside the predicted scope | **FAIL on fast-track** ("fast-track incident"), WARN otherwise |
| outcome `failed` | FAIL on fast-track, WARN otherwise |
| an audit file names the task id | WARN |
| maximum repair iterations used | WARN |
| major / blocking unknowns | INFO |

Verdict: any FAIL → **FAIL** (exit 2), any WARN → **ATTENTION** (exit 1), else **PASS** (exit 0).

**Scope accuracy.** Tests are excluded on both sides, since tests may always change:

- **recall** = predicted ∩ changed / changed: did the manifest anticipate everything that had to change? A miss is
  the expensive error: the change touched code nobody had analysed.
- **precision** = predicted ∩ changed / predicted: how much of the predicted scope was needed? Low precision costs
  review time, not safety.

The agent appends a cause, an owner and a fix for every FAIL / WARN. It never edits the numbers, and it never
back-fills missing evidence (writing a `verification.md` for checks that were not run is itself a FAIL of rule 10).

## 3. Pilot evaluation: `evaluate.py pilot [--since YYYY-MM-DD]`

It aggregates every manifest under `artifacts/changes/` and every episode in `artifacts/memory/episodes.jsonl`
(the latest line per task id wins), then applies the exit gates from `brownfield.evaluation` in `.claude/config.yaml`:

| Gate | Default | Fail means | Severity |
|---|---|---|---|
| recorded episodes | ≥ 5 | too little evidence to decide | WARN |
| fast-track incidents | ≤ 0 | the cheapest path let an unanalysed change through | FAIL |
| mean scope recall | ≥ 0.90 | manifests miss files that must change | FAIL |
| mean scope precision | ≥ 0.50 | manifests over-scope | WARN |
| success rate of executed changes | ≥ 0.80 | changes fail even with context | FAIL |
| change scorecards with FAIL | 0 | an evidence trail is broken | FAIL |

Other metrics in the report: workflow mix, outcomes, mean repair iterations, how many changes needed a scope
amendment, and **confidence calibration**, meaning the outcomes per confidence band (≥ 0.80, 0.60–0.79, < 0.60).
If the ≥ 0.80 band does not succeed clearly more often than the lower bands, the thresholds in
`brownfield.confidence` are not telling you anything for this repo. Re-tune them (a human decision, recorded in
`docs/harness/decisions.md`).

**Decision**, appended by `/evaluate-pilot`:

| Verdict | Recommendation | Then |
|---|---|---|
| PASS | **GO** | a human adds the next services to `brownfield.enabled_services` |
| ATTENTION | **EXTEND** | run more changes; the report says which gate is short |
| FAIL | **STOP** | fix the causes (seeds, business rules, tests, contracts, thresholds), then re-evaluate |

Thresholds are changed only by a human, never to make a pilot pass.

### Suggested pilot plan

| Week | Do | Evaluate |
|---|---|---|
| 0 | setup, fill the pilot service's gaps | setup checks |
| 1 | 2–3 small changes (expect fast-track) | `/evaluate-change` each |
| 2 | 2–3 medium changes (one touching a contract or another service) | `/evaluate-change` each |
| 3 | at least one `clarify` and one `guarded` change, to exercise the gates | `/evaluate-pilot` → GO / EXTEND / STOP |

## 4. Kit self-test

Run this after upgrading the kit or changing anything under `tools/context/` or `scripts/`.

**Engine tests.** The suites in `tools/context/reference-tests/` use inline fixtures only and pass in any repo:
`test_languages.py` (language adapters, convention presets, coverage formats, QA test cases),
`test_knowledge_base.py` (documents, exclusion of unsafe passages) and `test_discovery.py` (layout discovery).

```bash
python -m pytest tools/context/reference-tests -q    # every test passes; none is skipped
```

Integration tests that need one specific application's real graphs are kept with that application, never in the
kit; run them in a copy of that application after `install.py --apply --upgrade`.

**Portability smoke (any repo).** Run it in a throwaway clone of your repo, or in a small two-service repo, never in
the working copy the pilot is evaluated on. Smoke changes and episodes would be counted by `/evaluate-pilot`.

```bash
python tools/context/refresh.py --check                                   # 0
python tools/context/manifest.py --task "<small realistic change>" --id SMOKE-1 --seed <svc>:<module.function>
# make the change + a test, then
python tools/context/refresh.py --stale --tests
python tools/context/manifest.py --verify-scope SMOKE-1                   # 0 within scope
python tools/context/record_episode.py SMOKE-1 --outcome success
python tools/context/evaluate.py change SMOKE-1                           # findings only for artifacts you skipped
```

The tool writes only `context-manifest.yaml` and `impact-analysis.md`. The other artifacts come from the agents, so
a pure-CLI smoke reports them as missing. That is expected.

Kit 1.0.0 was verified this way on 2026-10-09: the full loop (setup → manifest → change → refresh → scope check →
episode → PASS scorecard) ran on a two-service sample repo with a non-default services root and no shared library.
