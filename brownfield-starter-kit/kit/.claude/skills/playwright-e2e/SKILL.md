---
name: playwright-e2e
description: Start verified local stack, run Playwright E2E against the live UI, route failures to owning agents. Use on /run-tests and /close-eval-gaps UI fixes.
---

# Playwright E2E

## Prerequisites

Application **must** be running before E2E:

```bash
bash scripts/run-local-stack.sh
bash scripts/verify-stack-health.sh
```

If health check fails → **environment FAIL**; owning agent: **backend-agent** (API) or **frontend-agent** (UI).

## Run

From config `evals.test_commands.e2e`, typically:

```bash
cd <ui-module-root>
npm run test:e2e
```

Use `channel: 'chrome'` when browser download is blocked. Default `--workers=1`.

## Authoring (playwright-codegen)

1. Every spec cites TC / AC / FR/BR from approved package.
2. Generate `e2e/fixtures`, `e2e/data`, page objects when missing.
3. Mirror API auth headers from IT tests — no invented journeys.

## On failure

| Failure type | Owning agent |
|--------------|--------------|
| Locator / UI regression | frontend-agent |
| API 4xx/5xx / wrong payload | backend-agent or api-agent |
| Environment / stack down | backend-agent + frontend-agent |

e2e-defect-analyzer → `artifacts/issues/<date>-e2e-failure.md`. playwright-self-healer → suggestion only (human applies).

## Subagents

`playwright-codegen`, `ui-test-runner`, `e2e-scenario-writer`, `e2e-defect-analyzer`, `playwright-self-healer`
