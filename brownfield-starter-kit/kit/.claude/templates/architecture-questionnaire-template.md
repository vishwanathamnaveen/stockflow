# Architecture Questionnaire — {{SESSION_ID}}

> Phase 1 of `/propose-architecture`. Log questions and answers to `artifacts/architecture/<date>-questionnaire-log.md`. Do not store secrets.

| Field | Value |
|-------|-------|
| **Date** | {{YYYY-MM-DD}} |
| **Operator** | {{name or role}} |
| **Inputs scanned** | {{BRD, story pack, config paths or none}} |

## Business and requirements

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 1 | What business capability or product is in scope? | | |
| 2 | Primary users and personas? | | |
| 3 | Expected scale (users, TPS, data volume)? | | |
| 4 | Compliance or regulatory tags (SOC2, PCI, etc.)? | | |
| 5 | Hard deadlines or phased rollout constraints? | | |

## Cloud and operations

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 6 | Cloud target (Azure / AWS / GCP / on-prem / hybrid)? | | |
| 7 | Multi-region or DR requirements? | | |
| 8 | Environment count (dev/stage/prod)? | | |
| 9 | Existing landing zone or greenfield? | | |
| 10 | Budget or managed-service preferences? | | |

## Tech stack

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 11 | Preferred backend stack (Java/Spring, Python, other)? | | |
| 12 | Preferred UI stack (Next.js, other)? | | |
| 13 | Data stores (relational, cache, search, blob)? | | |
| 14 | Messaging or event bus required? | | |
| 15 | Legacy systems that must integrate? | | |

## Architecture style

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 16 | Modular monolith vs microservices vs hybrid? | | |
| 17 | BFF layer (yes/no) and why? | | |
| 18 | Micro-frontends or single UI app? | | |
| 19 | Sync REST vs async events — primary integration? | | |
| 20 | Number of bounded contexts or services (initial)? | | |

## Client / server and security

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 21 | SSR vs CSR vs hybrid for UI? | | |
| 22 | Who calls APIs (browser, BFF, batch, partners)? | | |
| 23 | Identity provider or auth model known? | | |
| 24 | Data classification (PII, PCI, public)? | | |

## Team and delivery

| # | Question | Answer | Source if pre-filled |
|---|----------|--------|----------------------|
| 25 | Team topology (single squad vs platform + feature)? | | |
| 26 | Release cadence (continuous, sprint, train)? | | |
| 27 | Existing repo or greenfield codebase? | | |

## Unresolved after Q&A

| DQ ID | Item | Owner |
|-------|------|-------|
| | | |

**Log output path:** `artifacts/architecture/{{YYYY-MM-DD}}-questionnaire-log.md`
