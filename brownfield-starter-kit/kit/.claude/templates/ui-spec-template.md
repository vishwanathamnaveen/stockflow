# UI Specification — {{SCREEN_OR_FLOW}}

> From `/generate-ui-design` or story pack UX tables. Cite Figma or approved UX source — do not invent microcopy.

| Field | Value |
|-------|-------|
| **Screen / flow** | {{name}} |
| **Figma ref** | {{url + node-id}} or N/A |
| **Story / AC refs** | {{ids}} |
| **Status** | Draft / Review / Approved |
| **Author** | frontend-agent / business-analyst-agent |

## Purpose

- **User goal:**
- **Entry points:**
- **Exit points:**

## Layout regions

| Region | Content | Component mapping |
|--------|---------|-------------------|
| header | | |
| main | | |
| footer / actions | | |

## States

| State | Trigger | Visual / behavior | API dependencies |
|-------|---------|-------------------|------------------|
| empty | no data | | GET … |
| loading | fetch | skeleton | |
| populated | data loaded | | |
| error | API 4xx/5xx | cite error copy source | |
| validation | form invalid | | |

## Fields and validation

| Field | Label (source) | Type | Required | Validation rules (cite BR) | Error message (source) |
|-------|----------------|------|----------|----------------------------|------------------------|
| | | text/select/… | yes/no | | |

## Actions

| Action | Label | Enabled when | API call | Success | Failure UX |
|--------|-------|--------------|----------|---------|------------|
| Submit | | | POST … | navigate … | |

## Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Focus order | |
| Keyboard | |
| Screen reader labels | |
| Contrast | WCAG AA |

## Responsive behavior

| Breakpoint | Changes |
|------------|---------|
| mobile | |
| tablet | |
| desktop | |

## Copy provenance

| UI string | source_path | locator |
|-----------|-------------|---------|
| | | |

## Open gaps

| DQ ID | Gap | Owner |
|-------|-----|-------|
| | | |

**Output path:** `docs/ux/{{flow}}/ui-behavior-spec.md` or `docs/sprint{{N}}/ui-spec-{{slug}}.md`
