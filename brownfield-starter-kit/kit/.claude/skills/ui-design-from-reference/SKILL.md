---
name: ui-design-from-reference
description: Website reference URL + sprint screen → mockup PNG for /generate-ui-design and /implement-ui.
---

# UI design from reference

## When to use

`/generate-ui-design` only. Not Figma DS extract (`/generate-ui-design`) or static sketch ingest (`/generate-ui-design`).

## Phases

1. **Capture** — `tools/design/capture-reference.py --url <url> [--path /page] [--viewport desktop]` or operator `screenshot_path`.
2. **Brief** — `ui-design-brief-writer` fills `ui-design-brief-template.md`.
3. **Mockup** — `ui-mockup-generator` produces PNG; optional image generation when available.

## Outputs

- `artifacts/design/<date>-reference-capture.png`
- `artifacts/design/<date>-design-brief.md`
- `artifacts/design/<date>-<feature>-mockup.png`
- `artifacts/design/<date>-mockup-manifest.json`

## Provenance

Cite sprint SP/AC for fields. Uncited visible text → `[Label]` placeholder.

## Must NOT

- Generate production components
- Bypass Approved plan gate
