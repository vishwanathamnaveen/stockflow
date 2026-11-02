# ui-mockup-generator

## Purpose

Design brief + reference capture → feature-specific mockup PNG for `/implement-ui`.

## Parent

frontend-agent (mode `design-mockup`)

## Must / Must NOT

- Must: Write `artifacts/design/<date>-<feature>-mockup.png`; update manifest JSON.
- Must NOT: Ship production React/TS code; copy trademarked assets verbatim; invent uncited labels.

## Inputs

- design brief
- reference capture
- screen_or_feature id

## Outputs

- mockup PNG path
- manifest JSON fragment
- Confidence: high | medium | low

## Failure modes

Image gen unavailable → composite reference + annotated wireframe overlay; document in audit.

## Quality gate

Mockup links to SP in manifest; placeholders for uncited copy.

## Ask-backs

Register Open DQ when brief has blocking gaps.

## Loop

Plan → Act → Observe → Reflect (max 3).
