# /generate-ui-design

## Objective

Reference **website URL** + sprint screen/feature → mockup **PNG** + design brief for `/implement-ui`. Does not author requirements or production React code.

## Distinct from

| Input | Command |
|-------|---------|
| User already has PNG/screenshot | `/generate-ui-design` |
| Figma Design System file URL | `/generate-ui-design` |
| **Website URL as design reference** | **this command** |

## Runtime Inputs

### Required

- `reference_url` — public website for layout/style inspiration
- `screen_or_feature` — SP item or screen from **Approved** sprint plan

### Optional

- `reference_path` (e.g. `/pricing`)
- `viewport` (desktop / tablet / mobile)
- `governed_plan` / sprint plan path
- `screenshot_path` — fallback when URL blocked (login, CAPTCHA)

## Plan-as-input mode

When `governed_plan` or `sprint_governed_plan` is supplied, apply `.claude/templates/plan-as-input-protocol.md` before Phase 1.

## Use Agents

orchestrator-agent → frontend-agent (mode `design-mockup`)

## Delegate to Subagents

reference-site-capturer → ui-design-brief-writer → ui-mockup-generator

## Enforce Rules

04, 10, 22, 31 (sidecar text notes only)

## Use Templates

`ui-design-brief-template.md`, `ui-mockup-manifest-template.md`, `audit-trail-template.md`, `plan-act-observe-reflect-loop.md`

## Use Skills

`.claude/skills/ui-design-from-reference/SKILL.md`

## Execution Policy

Plan → Act → Observe → Reflect (max 3). Iteration 1 Observe pass → stop.

### Phases

1. **Capture** — `reference-site-capturer` → `artifacts/design/<date>-reference-capture.png` (or use operator `screenshot_path`)
2. **Brief** — `ui-design-brief-writer` → `artifacts/design/<date>-design-brief.md`
3. **Mockup** — `ui-mockup-generator` → **`artifacts/design/<date>-<feature>-mockup.png`**

## Clarification Protocol

If `reference_url` or `screen_or_feature` missing, ask with **recommendation** (e.g. default SP from plan). If site requires auth, register Open DQ; ask for `screenshot_path`. Do not invent copy — use `[Label]` placeholders. Do not STOP except human gates. Refuse when plan is not **Approved**.

## Command-Specific Hardening

- Must NOT ship production UI code (that is `/implement-ui`).
- Must NOT copy trademarked assets verbatim.
- Run `python3 tools/design/capture-reference.py` when URL capture is used (or browser MCP equivalent).
- Mockup must link to SP item in manifest JSON.

## Definition of Done

- [ ] Reference capture or operator screenshot documented
- [ ] Design brief cites plan AC + visible reference elements
- [ ] Mockup PNG written
- [ ] Manifest JSON links mockup → SP → reference URL
- [ ] `artifacts/audit/<date>-generate-ui-design-<task>.md` written

## Required Output

- `artifacts/design/<date>-reference-capture.png` (when capture ran)
- `artifacts/design/<date>-<feature>-mockup.png`
- `artifacts/design/<date>-design-brief.md`
- `artifacts/design/<date>-mockup-manifest.json`

## Next command

> ✅ `/generate-ui-design` complete.
> **Next command:** `/implement-ui` with `mockup_path` = mockup PNG above.
