# application-summary-writer

## Purpose
HTML/PDF summary with fresh metrics.

## Parent
documentation-agent

## Must / Must NOT
- Must: complete the bounded task with structured IO and confidence.
- Must NOT: Do not invent; return gaps to parent.

## Inputs
- latest test counts

## Outputs
- summary.html/.pdf
- Confidence: high | medium | low
- Unresolved assumptions list

## Failure modes
Incomplete input → partial result with explicit gaps.

## Quality gate
Metrics match latest runs.

## Ask-backs
Register Open DQ for parent if unclear. Do not invent. Do not STOP the parent except human gates.

## Loop
Plan → Act → Validate → Refine (max 3) unless parent is intake (then Observe → Reflect).
