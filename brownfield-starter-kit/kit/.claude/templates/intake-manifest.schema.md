# Intake manifest schema

Written by `test-intake-normalizer` to `artifacts/test-intake/<YYYY-MM-DD>-manifest.json`.

Trusted factory artifacts (BRD, stories, OpenAPI, checklists) are listed with `"scan": "skipped"`. Untrusted sources (Figma extract, Excel, CSV) must be persisted under `artifacts/test-intake/` and scanned with `python3 scripts/intake-safety-scan.py` before case authoring.

```json
{
  "scope": "sprint-item-or-story-pack",
  "date": "2026-09-11",
  "sources": [
    {
      "kind": "checklist | brd | stories | openapi | figma | excel | csv",
      "path": "repo-relative path",
      "trusted": true,
      "scan": "skipped | clean | review | block",
      "scan_exit_code": 0,
      "notes": ""
    }
  ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `scope` | yes | Sprint item, story pack, or bounded-context id |
| `date` | yes | ISO date of this intake run |
| `sources[].kind` | yes | One of the enum values above |
| `sources[].path` | yes | Repo-relative; Figma extracts must be markdown on disk before scan |
| `sources[].trusted` | yes | `true` for BRD/stories/OpenAPI/checklists already in-repo |
| `sources[].scan` | yes | `skipped` only when `trusted` is true |
| `sources[].scan_exit_code` | when scanned | 0 clean, 1 PII review, 2 injection block |
| `sources[].notes` | no | Redaction owner, conversion (xlsx→csv), DQ ids |

Excel `.xlsx` is not scannable. Convert to CSV in the intake folder, then scan the CSV. Do not store PII values in `notes`.
