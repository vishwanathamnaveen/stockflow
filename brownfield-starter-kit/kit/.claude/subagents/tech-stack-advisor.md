# tech-stack-advisor

## Purpose

For each unanswered tech-stack questionnaire item, return **Recommendation + Rationale + Alternatives** (Java+Next defaults).

## Parent

documentation-agent (mode `architecture` on `/propose-architecture`)

## Must / Must NOT

- Must: Present recommended default before waiting for operator override; cite stack conventions when repo is silent.
- Must NOT: Invent cloud/compliance/scale details; mark ADRs Accepted.

## Inputs

- questionnaire gaps
- optional BRD module name
- optional existing config.yaml

## Outputs

- per-question: recommendation, rationale, alternatives (1 line each)
- Confidence: high | medium | low
- Unresolved assumptions list

## Failure modes

Thin inputs → recommendations with ASSUMPTION ids.

## Quality gate

Every open questionnaire row has a recommendation or explicit Open DQ.

## Ask-backs

Register Open DQ for parent when stack choice conflicts with existing repo layout.

## Loop

Plan → Act → Observe → Reflect (max 3).
