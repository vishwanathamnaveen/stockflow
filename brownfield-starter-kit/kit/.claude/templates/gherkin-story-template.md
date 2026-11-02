# Gherkin Story — {{STORY_ID}}

> BDD slice from business-analyst-agent / gherkin-writer. Every scenario traces to AC.

| Field | Value |
|-------|-------|
| **Story ID** | {{SP-xxx}} |
| **Title** | {{title}} |
| **AC refs** | {{AC-ids}} |
| **Source** | {{story pack path}} |

## User story

As a **{{role}}**, I want **{{capability}}**, so that **{{benefit}}**.

## Background

```gherkin
Given ...
```

## Scenarios

### Scenario: {{happy path title}}

```gherkin
@AC-01 @positive
Scenario: ...
  Given ...
  When ...
  Then ...
```

### Scenario: {{negative / edge title}}

```gherkin
@AC-01 @negative
Scenario: ...
  Given ...
  When ...
  Then ...
```

## Data examples (if Scenario Outline)

| col1 | col2 | expected |
|------|------|----------|
| | | |

## API / UI dependencies

| Step | Dependency |
|------|------------|
| Given user logged in | auth fixture / API |

## Traceability

| Scenario tag | AC | Test case ID |
|--------------|----|--------------|
| @AC-01 | AC-01 | TC- |

**Output path:** Section in techno-functional pack or `docs/stories/{{id}}.feature`
