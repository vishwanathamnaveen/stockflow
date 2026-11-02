# Onboarding checklist: day 0 to pilot exit

Repo: ____________  Tech lead: ____________  Pilot service: ____________  Start date: ____________

## Day 0: decide
- [ ] Pilot service chosen: has tests, an owner, and changes coming up
- [ ] Owner named for every service (or knowingly `TBD`, which makes that service `guarded`)
- [ ] One business-language description per service written by a human
- [ ] Documents for `knowledge/` collected and confirmed free of personal / regulated data (or none)
- [ ] Repo layout matched to a recipe in `docs/LAYOUT-RECIPES.md`: ____

## Day 1: install and set up ([01-SETUP.md](../docs/01-SETUP.md))
- [ ] `install.py <repo>` dry run read; `--apply` run; `keep (differs)` files reviewed
- [ ] `python scripts/setup_toolchain.py` exits 0 (venv, locked packages, model, offline smoke); its python activated
- [ ] `install.py <application folder> --apply` ran; discovered layout reviewed (`python tools/context/discover.py`);
      owners and descriptions written in `config/services.yaml` (git is optional)
- [ ] each service's `test_command` + `coverage` agreed (Python: default pytest); `python scripts/run_tests.py` green
- [ ] `python tools/context/conventions.py`: languages and presets per service look right (routes, handlers, tables)
- [ ] QA test cases: `brownfield.test_cases` set when they live elsewhere; `python tools/context/test_cases.py` loads them
- [ ] Claude Code opened at the repo root; `/setup-context` listed
- [ ] `/setup-context` gate 1: registry, layout and scaffold list confirmed
- [ ] stages a–f exit 0 (failing suites listed, not "fixed")
- [ ] `refresh.py --check` exit 0; smoke search and smoke manifest pass
- [ ] `artifacts/audit/<date>-setup-context.md` exists

## Days 2–3: close gaps on the pilot service
- [ ] OpenAPI contract present (if it has an API)
- [ ] business rules a human confirmed, in `docs/business-rules.md`
- [ ] test suite green, with per-test coverage present
- [ ] `contracts/events.yaml` strict YAML (if it has events)
- [ ] `/refresh-context` after the gap fixes; `--check` exit 0
- [ ] pilot service added to `brownfield.enabled_services` (human edit)
- [ ] decided whether to commit graphs and add `refresh.py --check --committed-only` to CI: ____

## Weeks 1–3: pilot ([02-CHANGE-FLOW.md](../docs/02-CHANGE-FLOW.md))
- [ ] team walked through one change together (fast-track)
- [ ] ≥ 5 change requests through `/build-context` → gate → `/implement-change` → `/evaluate-change`
- [ ] at least one `clarify`, one `plan-approve-execute` and one `guarded` change, so every gate is exercised
- [ ] every episode recorded with a lesson where something surprised you

## Pilot exit ([03-EVALUATION.md](../docs/03-EVALUATION.md))
- [ ] `/evaluate-pilot` run: verdict ____  (GO / EXTEND / STOP)
- [ ] calibration table reviewed; `brownfield.confidence` re-tuned or kept, with a dated entry in `docs/harness/decisions.md`
- [ ] next services to enable: ____________ (human edit of `enabled_services`)
- [ ] retro: top 3 lessons shared with the next team
