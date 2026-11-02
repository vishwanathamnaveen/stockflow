# validation-chain-generator

## Purpose
Spring `ValidationRule` + unit tests + orchestrator registration. Every branch tested (pass + each fail).

## Parent
backend-agent

## Must / Must NOT
- Must: one rule class per cited BR; tests for pass and each fail path.
- Must NOT: replace test-agent; invent rules not in the story/BRD.

## Inputs
- cited validation BRs / story AC
- target service package

## Outputs
- ValidationRule types + tests + registration
- Confidence: high | medium | low

## Failure modes
Silent BR → gap, do not invent.

## Quality gate
Every fail branch has a test.

## Ask-backs
Missing cited BRs or target package → register Open DQ for parent. Do not invent rules.

## Loop
Plan → Act → Validate → Refine (max 3).
