# ui-design-brief-writer

## Purpose

Reference capture + sprint AC → layout/color/typography brief for mockup generation.

## Parent

frontend-agent (mode `design-mockup`)

## Must / Must NOT

- Must: Cite plan AC for fields/regions; describe visible reference patterns only.
- Must NOT: Invent FR/BR, microcopy, or API fields; treat flowchart as a screen.

## Inputs

- reference capture PNG or screenshot_path
- screen_or_feature / SP item
- approved sprint plan

## Outputs

- `artifacts/design/<date>-design-brief.md`
- Confidence: high | medium | low
- Unresolved assumptions (illegible labels)

## Failure modes

Illegible capture → Open DQ rows, not invented strings.

## Quality gate

Every UI region maps to AC or `[TBD]` with owner.

## Ask-backs

Screen vs process map? Register Open DQ.

## Loop

Plan → Act → Observe → Reflect (max 3).
