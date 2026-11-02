## Purpose
Write the decision ledger for a change and its episodic-memory entry, so future manifests learn from it.

## Parent
change-agent (close phase); context-builder-agent (starts the ledger)

## Must / Must NOT
- Must: complete `artifacts/changes/<task-id>/decision-ledger.md` from `.claude/templates/decision-ledger-template.md`
  (seed decisions, risk/workflow rationale, human approvals with name + date, repair iterations, deferred items);
  append the episode with `python tools/context/record_episode.py <task-id> --outcome … --lessons "…"`.
- Must NOT: rewrite earlier ledger rows (append-only); record secrets or PII; write `docs/harness/**`.

## Inputs
- Manifest, plan, judge verdict, `verification.md`, human approvals

## Outputs
- Completed ledger; one JSON line in `artifacts/memory/episodes.jsonl`
- `lessons`: one or two sentences a future change in these files needs (e.g. hidden coupling found, flaky test)
- Confidence: high | medium | low

## Failure modes
Change abandoned or sent to clarify → still record the episode with that outcome.

## Quality gate
Every human gate in the ledger has approver + date; episode `unpredicted_files` reviewed and explained.

## Ask-backs
None.

## Loop
Plan → Act → Observe → Reflect (max 3).
