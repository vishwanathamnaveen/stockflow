"""External test cases (QA repositories, test-management exports) linked to the code a change touches.

    python tools/context/test_cases.py                      # list the configured sources and what they contain
    python tools/context/test_cases.py --covers OrderServiceImpl.approve "POST /api/v1/orders/{id}/approval"

Configured in .claude/config.yaml (paths are relative to the repo root; a sibling QA repo is fine):

    brownfield:
      test_cases:
        - {path: ../orders-qa/testcases, format: zephyr-json}
        - {path: ../orders-qa/features,  format: gherkin}
        - {path: qa/export.csv,          format: csv}

Formats (`auto` picks by file suffix): zephyr-json / xray-json / json (any JSON test-case shape: key, name and a
`Covers`-like traceability field are found by name), gherkin (`.feature`: scenario tags carry the case key, a
`# Covers:` comment the traceability), csv (columns found by header name).

A case is linked to a change through its traceability field (`Covers`: endpoints such as
`POST /api/v1/orders/{id}/approval`, classes `OrderApproval`, methods `OrderServiceImpl.approve`, fields
`OrderApproval.rejectionReason`) and, when it has none, through endpoints named in its steps. The manifest lists:

  direct      the case covers a changed symbol, its class, a changed API or a changed field: its assertions may
              need updating (review it; the change-agent proposes the edit)
  transitive  the case covers code that depends on the change: run it as regression

Which cases must change and which new ones are needed stays a human / agent judgement: this is the evidence.
Test-case text is untrusted data (rule 31): it is matched, never followed.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

KEY_PATTERN = r"[A-Z][A-Z0-9_]*-(?:T|TC|C)?\d+"
COVERS_KEYS = re.compile(r"^(covers?|coverage|traceability|traces?|linked[_ ]?(code|items)|code[_ ]?refs?|"
                         r"automation[_ ]?refs?|components?[_ ]?covered)$", re.I)
ENDPOINT = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_{}/.:\-]*)")


def _split(value) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in re.split(r"[;\n]|,(?![^{]*\})", value) if v.strip()]
    return []


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def _find_covers(value) -> list[str]:
    if isinstance(value, dict):
        for k, v in value.items():
            if COVERS_KEYS.match(str(k)):
                return _split(v)
        for v in value.values():
            found = _find_covers(v)
            if found:
                return found
    return []


def _json_case(data: dict, file: str) -> dict | None:
    key = next((str(data[k]) for k in ("key", "testKey", "issueKey", "id", "testCaseKey") if data.get(k)), None)
    name = next((str(data[k]) for k in ("name", "summary", "title") if data.get(k)), None)
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    name = name or fields.get("summary")
    if not key and not name:
        return None
    folder = data.get("folder") if isinstance(data.get("folder"), str) else (data.get("folder") or {}).get("name") \
        if isinstance(data.get("folder"), dict) else None
    labels = data.get("labels") or fields.get("labels") or []
    return {"key": key or f"{Path(file).stem}", "name": name or key, "file": file, "folder": folder,
            "priority": (data.get("priority") or {}).get("name") if isinstance(data.get("priority"), dict) else data.get("priority"),
            "labels": labels if isinstance(labels, list) else _split(labels),
            "covers": _find_covers(data), "text": " ".join(_strings(data))[:20000]}


def load_json_file(path: Path, file: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("values") or data.get("tests") or data.get("testCases") \
        or [data] if isinstance(data, dict) else []
    return [c for c in (_json_case(d, file) for d in items if isinstance(d, dict)) if c]


def load_feature(path: Path, file: str, key_pattern: str = KEY_PATTERN) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cases, feature_tags, tags, comments = [], [], [], {}
    current = None
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith("@"):
            tags += [t.lstrip("@") for t in line.split() if t.startswith("@")]
            continue
        m = re.match(r"#\s*(\w[\w ]*?)\s*:\s*(.*)$", line)
        if m:
            comments[m.group(1).lower()] = m.group(2)
            continue
        if line.startswith("Feature:"):
            feature_tags, tags = tags, []
            continue
        m = re.match(r"(Scenario(?: Outline| Template)?|Example):\s*(.*)$", line)
        if m:
            if current:
                cases.append(current)
            key = next((t for t in tags if re.fullmatch(key_pattern, t)), None)
            current = {"key": key or f"{Path(file).stem}:{n}", "name": m.group(2).strip(), "file": f"{file}:{n}",
                       "folder": next((t[len("component-"):] for t in feature_tags if t.startswith("component-")), None),
                       "priority": next((t[len("priority-"):] for t in tags if t.startswith("priority-")), None),
                       "labels": [t for t in tags if t != key], "covers": _split(comments.get("covers", "")),
                       "text": " ".join([m.group(2), comments.get("objective", "")])}
            tags, comments = [], {}
            continue
        if current and line:
            current["text"] += " " + line
    if current:
        cases.append(current)
    return cases


def load_csv(path: Path, file: str) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return []
    headers = {h.lower().strip(): h for h in rows[0].keys() if h}
    pick = lambda *names: next((headers[n] for n in names if n in headers), None)  # noqa: E731
    key_h, name_h = pick("key", "id", "test key", "test id", "issue key"), pick("name", "title", "summary")
    covers_h = next((h for low, h in headers.items() if COVERS_KEYS.match(low.replace(" ", "_"))), None)
    out = []
    for i, row in enumerate(rows, 2):
        out.append({"key": (row.get(key_h) or f"{Path(file).stem}:{i}") if key_h else f"{Path(file).stem}:{i}",
                    "name": row.get(name_h) or "", "file": f"{file}:{i}", "folder": row.get(pick("folder", "component") or ""),
                    "priority": row.get(pick("priority") or ""), "labels": _split(row.get(pick("labels") or "") or ""),
                    "covers": _split(row.get(covers_h) or "") if covers_h else [],
                    "text": " ".join(str(v) for v in row.values() if v)[:20000]})
    return out


FAMILY = {"auto": None, "json": "json", "zephyr-json": "json", "xray-json": "json", "testrail-json": "json",
          "gherkin": "gherkin", "csv": "csv"}


def _format_of(path: Path, declared: str) -> str | None:
    if declared not in ("auto", None):
        return FAMILY[declared]
    return {".json": "json", ".feature": "gherkin", ".csv": "csv"}.get(path.suffix.lower())


def load(sources: list[dict], root: Path, rel) -> tuple[list[dict], list[dict]]:
    """All cases from all sources -> (cases, per-source summary). Unreadable files are reported, not skipped silently."""
    cases, summary = [], []
    for src in sources:
        base = (root / src["path"]).resolve()
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []
        loaded, errors = 0, []
        declared = FAMILY.get(src.get("format") or "auto")
        for path in files:
            fmt = _format_of(path, "auto")              # by suffix; a declared format only filters
            if fmt is None or (declared and fmt != declared):
                continue
            try:
                found = {"json": load_json_file, "gherkin": load_feature, "csv": load_csv}[fmt](path, rel(path))
            except (ValueError, UnicodeDecodeError, KeyError, csv.Error) as exc:
                errors.append(f"{rel(path)}: {str(exc)[:80]}")
                continue
            for case in found:
                case["source"] = src["path"]
                case["format"] = src.get("format", "auto")
            cases += found
            loaded += len(found)
        summary.append({"path": src["path"], "format": src.get("format", "auto"), "exists": base.exists(),
                        "cases": loaded, **({"errors": errors[:5]} if errors else {})})
    return cases, summary


# --------------------------------------------------------------------------- linking


def _norm_path(path: str) -> str:
    return re.sub(r"\{[^}]*\}|:\w+|<[^>]+>", "{}", path.rstrip("/")) or "/"


def _path_matches(template: str, concrete: str) -> bool:
    if _norm_path(template) == _norm_path(concrete):
        return True
    rx = "^" + re.sub(r"\\\{\\\}", r"[^/]+", re.escape(_norm_path(template))) + "/?$"
    return bool(re.match(rx, concrete.rstrip("/") or "/"))


def _endpoint(item: str) -> tuple[str, str] | None:
    m = ENDPOINT.match(item.strip())
    return (m.group(1), m.group(2)) if m else None


def link(cases: list[dict], *, direct: list, transitive: list, apis: list[tuple[str, str]], fields: list[str],
         classes_of_fields: set[str], topics: list[str], reached_apis: list[tuple[str, str]] | None = None) -> list[dict]:
    """Cases whose traceability (or, failing that, step text) touches the change. `direct` / `transitive` are
    Symbol objects; `apis` (METHOD, path) pairs whose handler or contract shape changes, `reached_apis` the ones only
    reached through a changed dependency; `fields` changed field names."""
    reached_apis = reached_apis or []
    def names(syms) -> dict[str, set[str]]:
        out = {}
        for s in syms:
            owner = s.qualname.rsplit(".", 1)[0] if "." in s.qualname else None
            keys = {s.qualname, s.label()}
            if s.kind == "class":
                keys.add(s.name)
            out[s.key] = keys | ({owner} if owner and s.kind != "class" else set())
        return out

    d_names, t_names = names(direct), names(transitive)
    d_flat = {n for ns in d_names.values() for n in ns}
    t_flat = {n for ns in t_names.values() for n in ns} - d_flat
    field_set = set(fields)
    out = []
    for case in cases:
        via, tier = [], None
        for item in case["covers"]:
            clean = item.strip().rstrip("()").strip()
            ep = _endpoint(clean)
            if ep:
                if any(m == ep[0] and _path_matches(p, ep[1]) for m, p in apis):
                    via.append(f"covers API {clean}")
                    tier = "direct"
                elif any(m == ep[0] and _path_matches(p, ep[1]) for m, p in reached_apis):
                    via.append(f"covers API {clean} (reached through the change)")
                    tier = tier or "transitive"
                continue
            leaf = clean.split(".")[-1]
            if clean in d_flat:
                via.append(f"covers {clean}")
                tier = "direct"
            elif "." in clean and leaf in field_set and (clean.split(".")[-2] in classes_of_fields or not classes_of_fields):
                via.append(f"covers changed field {clean}")
                tier = "direct"
            elif clean in topics:
                via.append(f"covers event {clean}")
                tier = "direct"
            elif clean in t_flat:
                via.append(f"covers {clean} (depends on the change)")
                tier = tier or "transitive"
        if not case["covers"]:
            for m in ENDPOINT.finditer(case["text"]):
                if any(m.group(1) == am and _path_matches(ap, m.group(2)) for am, ap in apis):
                    via.append(f"step text: {m.group(1)} {m.group(2)}")
                    tier = "direct"
                    break
                if any(m.group(1) == am and _path_matches(ap, m.group(2)) for am, ap in reached_apis):
                    via.append(f"step text: {m.group(1)} {m.group(2)} (reached through the change)")
                    tier = tier or "transitive"
        if tier:
            out.append({"key": case["key"], "name": case["name"], "file": case["file"], "tier": tier,
                        "via": sorted(set(via)), **({"folder": case["folder"]} if case.get("folder") else {}),
                        **({"priority": case["priority"]} if case.get("priority") else {})})
    # the same case exported twice (Zephyr JSON + Gherkin) is one case: merge evidence, keep the strongest tier
    merged: dict[str, dict] = {}
    order = {"direct": 0, "transitive": 1}
    for case in out:
        prev = merged.get(case["key"])
        if prev is None:
            merged[case["key"]] = {**case, "file": [case["file"]]}
            continue
        prev["file"].append(case["file"])
        prev["via"] = sorted(set(prev["via"]) | set(case["via"]))
        if order[case["tier"]] < order[prev["tier"]]:
            prev["tier"] = case["tier"]
    for case in merged.values():
        case["file"] = case["file"][0] if len(case["file"]) == 1 else case["file"]
    return sorted(merged.values(), key=lambda c: (order[c["tier"]], _key_order(c["key"])))


def _key_order(key: str):
    """CAS-T9 before CAS-T10."""
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", key)]


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import common
    sources = common.test_case_sources()
    if not sources:
        print("no brownfield.test_cases sources configured in .claude/config.yaml")
        return 0
    cases, summary = load(sources, common.ROOT, common.rel)
    for s in summary:
        print(f"{s['path']:<45} {s['format']:<12} exists={s['exists']}  cases={s['cases']}  {s.get('errors', '')}")
    if "--covers" in argv:
        wanted = argv[argv.index("--covers") + 1:]
        for case in cases:
            hit = [c for c in case["covers"] if any(w in c for w in wanted)]
            if hit:
                print(f"  {case['key']:<10} {case['name'][:60]:<60} {hit}")
    else:
        no_covers = [c["key"] for c in cases if not c["covers"]]
        print(f"{len(cases)} cases, {len(cases) - len(no_covers)} with a traceability field"
              + (f"; without: {', '.join(no_covers[:10])}" if no_covers else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
