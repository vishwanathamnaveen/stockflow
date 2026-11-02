# Plan → Act → Observe → Reflect

Use for **intake, reverse engineering, research**. Max **3** iterations. Max 3 is a **ceiling**, not a quota.

## Plan
Load sources and command contract. Register Open DQ if sources or scope are missing after resolve-before-ask. Still refuse when a Required input is absent. Do not invent.

## Act
Extract facts with citations (path, locator, quote or paraphrase tagged `[CITED]`). Register `[INFERRED]` only with a DQ-id.

## Observe
Compare extract against all sources. Flag conflicts. Build discussion coverage / provenance tables. Note silences as gaps, not features. **Never skip Observe.**

## Reflect
**Only from findings.** Revise the artifact when Observe found gaps, conflicts, or uncited claims: drop uncited claims, add open questions, lower confidence where sources disagree. Increment iteration.
If Observe is already clean (every behavior has provenance or an open question), do not Reflect.

## Exit
- Iteration 1 Observe meets the exit criteria below → **stop**. Do not start iteration 2 or 3.
- Findings remain → Reflect, then Act again (count includes the first pass; max 3).
- Still unmet after iteration 3 → escalate unresolved Blocking DQs.

Every behavior has provenance **or** an open question. Never self-approve a BRD or rule catalog.

Record `iteration` in the audit (use `1` when the first Observe passed).

## Completion
Write audit. Update harness on phase change. Tell the user **Next command**.
