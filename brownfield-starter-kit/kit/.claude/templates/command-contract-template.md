# Command Contract Template

Canonical schema for every slash command. Tailor Runtime Inputs, hardening, Clarification Protocol, and Definition of Done.

## Objective
What the command produces, for whom, and which pipeline phase.

## Runtime Inputs

### Required
Named inputs (`implementation_module_root`, `brd_path`, `sprint_id`, …).

### Optional
Defaults, `governed_plan`, `sprint_governed_plan`, `@story_artifact`, `plan_step`.

## Plan-as-input mode
When `governed_plan` / `sprint_governed_plan` / `@story_artifact` is supplied, load `.claude/skills/plan-as-input/SKILL.md` and apply resolve-before-ask in `plan-as-input-protocol.md` **before** Clarification Protocol.

## Use Agents
Primary agent path(s).

## Delegate to Subagents
Ordered list.

## Enforce Rules
`.claude/rules/*.mdc` relevant to this command only.

## Use Templates / Skills
Paths.

## Required Output
Concrete artifact paths.

## Command-Specific Hardening
Dos, don'ts, validators, stop conditions.

## Execution Policy
Loop: Plan → Act → Validate → Refine (or Observe → Reflect for intake). Max 3 is a ceiling. Iteration 1 Validate/Observe pass → stop. Refine/Reflect only from findings. Never skip Validate/Observe. Escalate with owners after iteration 3.

## Clarification Protocol
After resolve-before-ask, register remaining gaps as Open DQ with owner. Do not invent. Do not STOP for a clarification round except human gates (BRD Accepted, plan Approved). Still refuse when a Required input is absent.

## Artifact Persistence
Canonical paths + metadata header (timestamp, iteration, validation summary, command version).

## Definition of Done
Purpose-specific checkboxes.

## Next command
Tell the user:

```
✅ /<command> complete.
**Next command:** /<next>
```

Conditional branches when a human gate applies.
