# mockup-to-component

## Purpose
PNG / screenshot / Figma **node image** / feature.md → layout resolution for `next-component-generator`. Screen UI only.

## Parent
frontend-agent (`/generate-ui-design`, `/implement-ui`)

## Must / Must NOT
- Must: inventory regions, labels, hierarchy; flag illegible text; pass structured layout to next-component-generator.
- Must NOT: invent copy; treat a flowchart as a page (whiteboard skill); extract a full design system (`/generate-ui-design`).

## Inputs
- mockup_path or screenshot or feature_ref

## Outputs
- layout notes under `artifacts/intake/supporting/`
- Confidence: high | medium | low
- Unresolved assumptions list (illegible labels)

## Failure modes
Illegible mockup → questions, not invented strings.

## Quality gate
No invented labels.

## Ask-backs
Is this a screen or a process map? What is the feature_ref? Register Open DQ; do not invent copy.

## Loop
Plan → Act → Observe → Reflect (max 3).
