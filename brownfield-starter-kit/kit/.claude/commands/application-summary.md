# /application-summary

## Objective
Delivery summary with fresh metrics; update harness.

## Runtime Inputs

### Required
- latest test-results
- review artifact

### Optional
- sprint id

## Plan-as-input mode
When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Clarification Protocol.

## Use Agents
orchestrator-agent → documentation-agent (mode summary)

## Delegate to Subagents
application-summary-writer, harness-updater, audit-trail-writer

## Enforce Rules
08, 09, 10

## Use Templates
application-summary-template.md

## Required Output
- artifacts/application-summary.html
- optional pdf
- harness update

## Command-Specific Hardening
Stay in scope.yaml. No secrets in artifacts. Ask back if required inputs missing.

## Execution Policy
Loop: Plan → Act → Validate → Refine. Max 3 is a ceiling. Iteration 1 Validate pass → stop. Refine only from findings. Escalate with owners after iteration 3.

## Clarification Protocol
After resolve-before-ask, register remaining gaps as Open DQ with owner. Do not invent. Do not STOP for a clarification round except human gates (BRD Accepted, plan Approved). Still refuse when a Required input is absent.

## Artifact Persistence
Canonical paths above plus `artifacts/audit/<date>-<command>-<task>.md`. Metadata: timestamp, iteration, validation summary.

## Definition of Done
- [ ] Metrics match latest runs
- [ ] `artifacts/audit/<date>-application-summary-<task>.md` written
- [ ] progress.md updated (harness-updater)

## Next command

> ✅ `/application-summary` complete.
> **Next command:** `/application-summary` or wait for the next sprint. Harness `progress.md` must show this phase Done.
