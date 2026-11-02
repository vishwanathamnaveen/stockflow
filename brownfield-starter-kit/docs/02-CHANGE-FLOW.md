# 2. One change request, end to end

For every engineer. Every requirement, bug fix, feature or refactor on existing code follows this flow (rule 40).
"Small" changes too: the fast-track workflow is the cheap path for those.

```
/build-context "<request>"   ─►  artifacts/changes/<id>/  ─►  GATE (by workflow)  ─►  /implement-change <id>  ─►  /evaluate-change <id>
```

## Step 1: `/build-context` builds the evidence

```
/build-context "Customers can cancel an order until it ships"            # new id CR-<date>-<slug>
/build-context "JIRA-123: invoice tax is rounded wrong" id=JIRA-123
/build-context "What would renaming Order.status touch?" mode=analyze     # estimate / triage only, never code
```

What happens, and who does it:

| # | Step | Done by | Result |
|---|---|---|---|
| 1 | Intake: safety scan, type, id | task-intake-classifier | `task.md` |
| 2 | Freshness: `refresh.py --check` on every service | tool | stale graphs are refreshed first |
| 3 | Discovery run: lexical + semantic seeds, graph expansion | `manifest.py` (tool) | first `context-manifest.yaml` |
| 4 | Seed refinement: the agent reads the code and confirms the landing points (`--seed svc:symbol`), max 3 runs | context-manifest-builder | refined manifest with `explicit_seeds` |
| 5 | Impact: direct, transitive, runtime, data, regression, plus the consumer effect per edge | impact-analyzer | `impact-analysis.md` |
| 6 | Risk + workflow confirmed or **escalated** (never relaxed) | risk-workflow-selector | `builder_notes` |
| 7 | Plan + ledger | context-builder-agent | `change-plan.md` (`Status: Ready` or `Clarify`), `decision-ledger.md` |

Explicit seeds matter: the post-change scope check (`--verify-scope`) re-runs them, so a manifest built from lexical
seeds only cannot be scope-checked.

**Read the result.** Open `impact-analysis.md` first, then `change-plan.md`. In the manifest, look at:

- `confidence.components` and `confidence.critical_gaps`, not just `overall`. Overall is a heuristic, not a probability.
- `unknowns`: `blocking` means `clarify`; `major` items must be answered in the plan.
- `services.impacted` and `dependencies.cross_service`: who else is affected.
- `risk.mandatory_gates`: contract, destructive data change, security-sensitive code, missing owner.

## Step 2: the gate (chosen by the workflow, not by you)

| Workflow | Selected when | Before code | After code |
|---|---|---|---|
| `analyze-only` | a must-change service is not enabled, or `mode=analyze` | no code: split the task or enable the service | none |
| `clarify` | confidence below `confidence.plan` (0.60), or a blocking unknown | no code: answer the numbered questions in `change-plan.md`, then rerun `/build-context` | none |
| `fast-track` | confidence ≥ 0.80, risk low, no mandatory gate, no critical gap | none | human reviews the diff |
| `plan-approve-execute` | anything else up to medium risk | human writes `Approval: Approved by <name> <YYYY-MM-DD>` in `change-plan.md` | human reviews the diff |
| `guarded` | high / critical risk, or a guarded gate | plan approved + **owner sign-off of every impacted service** | security review + human diff review |

A contract, event payload, persistence or business-rule change is never fast-track (rule 40.5).

## Step 3: `/implement-change <id>`

```
/implement-change CR-20261009-cancel-order
```

The change-agent:

1. **Refuses** if there is no manifest, the plan is not `Ready`, the approval is missing, the service is not enabled,
   or the manifest is stale.
2. Writes **tests first**: failing tests for each acceptance criterion, plus characterisation tests for touched code
   that has no coverage. A test that passes before the change proves nothing, so it gets strengthened.
3. Implements the plan, editing only the manifest's `files` (+ `supporting_files` where the plan says) and their
   tests.
4. Runs **`/refresh-context <id> --tests`**: rebuilds the graphs from the changed code, then
   `manifest.py --verify-scope <id>`. Exit 4 means the change grew beyond the manifest (a new consumer, file or gate);
   the agent then files a scope change (`manifest.py --amend <id> --add-seed ... --reason ...`), which recomputes risk
   and may need a new approval.
5. Runs every `workflow.required_checks` command and writes `verification.md`.
6. change-judge (diff vs manifest) + code-review-agent (+ security-agent if guarded); at most 3 repair iterations,
   then `needs_human`.
7. Records the episode: `record_episode.py <id> --outcome success --lessons "..."`. Future manifests that touch the
   same files show this lesson.
8. Close gate: `refresh.py --check` exits 0.

You then review the diff. The agent never commits or pushes.

## Step 4: `/evaluate-change <id>`

Writes `artifacts/changes/<id>/evaluation.md`: evidence trail complete? scope recall/precision? fast-track incident?
See [03-EVALUATION.md](03-EVALUATION.md). Takes seconds; do it for every change, including the ones that ended in
`clarify` (record the episode with `--outcome clarify` first).

## Keeping context fresh

Nothing refreshes on its own. Run `/refresh-context` (or `python tools/context/refresh.py --stale`):

- after pulling or switching branches
- after editing code, `docs/business-rules.md`, `contracts/**`, `config/**` or `knowledge/**` outside `/implement-change`
- whenever `refresh.py --check` exits 2

`/build-context` and `/implement-change` check freshness themselves and stop on stale graphs.

## Roles

| Role | Decides |
|---|---|
| Requester | the task text; answers `clarify` questions |
| Engineer | runs the commands; reviews every diff; records lessons |
| Service owner | approves `plan-approve-execute` / `guarded` plans for their service; signs off impacts on their service |
| Tech lead | `enabled_services`, thresholds in `brownfield.confidence` / `brownfield.evaluation`, runs `/evaluate-pilot` |

## CLI equivalents (no Claude Code, or debugging)

```bash
python tools/context/refresh.py --check                                   # 0 fresh, 2 stale, 3 locked, 1 failed
python tools/context/refresh.py --stale [--tests]                          # rebuild what changed
python tools/context/semantic_index.py search "cancel an order" -k 5      # where does this live?
python tools/context/manifest.py --task-file task.md --id CR-1 --seed orders:domain.cancel_order
python tools/context/manifest.py --verify-scope CR-1                      # 0 within scope, 4 grew
python tools/context/manifest.py --amend CR-1 --add-seed billing:invoice.void --reason "invoice must be voided"
python tools/context/record_episode.py CR-1 --outcome success --lessons "..."
python tools/context/evaluate.py change CR-1                              # 0 PASS, 1 ATTENTION, 2 FAIL
graphify query "how is an order confirmed?" --graph <services_root>/orders/graphify-out/graph.json
```

The agents add what the tools cannot: seed judgement, impact verification against source, plan writing, tests-first
implementation, review. Running the tools by hand gives you the evidence, not the governance.
