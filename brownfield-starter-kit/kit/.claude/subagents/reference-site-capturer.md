# reference-site-capturer

## Purpose

Navigate to `reference_url` (+ optional path) and capture viewport screenshot for design reference.

## Parent

frontend-agent (mode `design-mockup` on `/generate-ui-design`)

## Must / Must NOT

- Must: Write PNG to `artifacts/design/<date>-reference-capture.png`; record URL, viewport, timestamp.
- Must NOT: Scrape credentials; capture authenticated pages without operator login; store secrets in artifacts.

## Inputs

- reference_url
- optional reference_path, viewport
- optional screenshot_path fallback

## Outputs

- capture PNG path
- capture metadata (url, viewport, dimensions)
- Confidence: high | medium | low

## Failure modes

Blocked URL (login, CAPTCHA, 403) → return gap; parent asks for `screenshot_path`.

## Quality gate

PNG readable; no PII in filename or sidecar logs.

## Ask-backs

Site blocked? Register Open DQ; suggest operator screenshot.

## Loop

Plan → Act → Observe → Reflect (max 3).
