# Commands (12 shipped + 6 brownfield)

| Command | Phase | Primary |
|---------|-------|---------|
| `/generate-brd` | Intake | requirements-agent |
| `/propose-architecture` | Architecture (satellite) | planner-agent |
| `/plan-sprint` | Plan | planner-agent |
| `/generate-ui-design` | UI mockup from website reference | frontend-agent |
| `/implement-api` | Backend | backend-agent |
| `/implement-ui` | Frontend + wiring | frontend-agent |
| `/expand-test-coverage` | Test design | quality-agent |
| `/run-tests` | Test execution | quality-agent |
| `/run-eval` | Product AI eval | quality-agent |
| `/close-eval-gaps` | Eval fix loop (inner spine) | orchestrator-agent |
| `/review-changes` | Review | code-review-agent |
| `/application-summary` | Summary | documentation-agent |
| `/setup-context` | Brownfield onboarding (once per new repo): layout check, toolchain, first graphify + service graph + FAISS index + knowledge base | context-bootstrap-agent |
| `/build-context` | Brownfield: task → Context Manifest, impact, risk, workflow, plan | context-builder-agent |
| `/implement-change` | Brownfield: manifest-bounded code change + regression + ledger | change-agent |
| `/refresh-context` | Brownfield: refresh graphs + index from the working tree; post-change scope check | change-agent / context-builder-agent |
| `/evaluate-change` | Brownfield: final scorecard for one CR (evidence trail + scope recall/precision) | quality-agent |
| `/evaluate-pilot` | Brownfield: pilot scorecard vs exit gates, go / extend / stop | quality-agent |

Brownfield path (rule 40): `/setup-context` (once per new repo) → `/build-context <task>` → [gate per workflow] → `/implement-change <task-id>`
(which runs `/refresh-context <task-id>` after the last edit, before final validation) → `/evaluate-change <task-id>`;
at the end of the pilot `/evaluate-pilot`.

`/close-eval-gaps` is invoked from `/run-eval` when `fix-queue.json` has open `auto_fix: true` items. May also be run directly to resume the queue.

Brownfield guide: `docs/brownfield/` (copied by the starter kit installer).
