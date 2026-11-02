# Per-change checklist

Task id: ____________  Requester: ____________  Engineer: ____________

## Before code (`/build-context`)
- [ ] graphs fresh (`refresh.py --check` exit 0, or `/refresh-context` done)
- [ ] `task.md` states the acceptance criteria (or they are listed as unknowns)
- [ ] seeds confirmed by reading the code (`explicit_seeds` in the manifest)
- [ ] `impact-analysis.md` read: impacted services and consumers make sense
- [ ] `confidence.critical_gaps` empty, or addressed / accepted in the plan
- [ ] effective workflow: ____  (fast-track / plan-approve-execute / guarded / clarify / analyze-only)
- [ ] gate met: none (fast-track) / plan approved by ____ on ____ / owner sign-offs: ____

## During (`/implement-change`)
- [ ] failing tests written first, one per acceptance criterion; characterisation tests for uncovered touched code
- [ ] only manifest files + supporting files (where the plan says) + tests changed
- [ ] `/refresh-context <id> --tests` after the last edit; `--verify-scope` within scope (or `--amend` + re-approval)
- [ ] every `workflow.required_checks` command green; `verification.md` written
- [ ] change-judge PASS; code review has no blocking findings; security review if guarded
- [ ] episode recorded with lessons

## After
- [ ] human reviewed the diff
- [ ] `/evaluate-change <id>`: ____  (PASS / ATTENTION / FAIL); every finding has a cause, owner and fix
- [ ] `refresh.py --check` exit 0 at close
