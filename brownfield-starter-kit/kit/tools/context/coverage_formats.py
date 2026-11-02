"""Coverage reports of any ecosystem -> the one shape the context engine reads (var/quality/<suite>-coverage.json).

    python tools/context/coverage_formats.py <format> <report> <service-dir> <out.json>

Normalised shape (the coverage.py JSON subset the tools use):

    {"meta": {"format": "jacoco", "report": "...", "per_test": false},
     "files": {"<path relative to the service dir>": {"executed_lines": [..], "missing_lines": [..],
                                                     "contexts": {"<line>": ["<test id>", ...]}}}}

Formats:
  coverage-py  coverage.py JSON (pytest --cov --cov-context=test): per-test contexts kept
  jacoco       JaCoCo XML (Maven / Gradle jacocoTestReport): line counters; no per-test data
  cobertura    Cobertura XML (coverlet, pytest-cov --cov-report=xml, gcovr, Istanbul cobertura reporter)
  lcov         lcov.info (Istanbul / nyc / c8 / Jest, gcov, grcov, Dart); per-test when the file has TN: records
  go           Go coverprofile (go test -coverprofile=cover.out)
  istanbul     Istanbul coverage-final.json

Report paths (absolute, package-relative, module-relative) are matched to the service's source files by the
longest common path suffix; report files that match no source file are listed in meta.unmatched (never guessed).
Without per-test data the manifest still gets line coverage (test_evidence) and lists tests from static
references; it says so as an unknown.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

FORMATS = ("coverage-py", "jacoco", "cobertura", "lcov", "go", "istanbul")


class Resolver:
    """Map a path as written by a coverage tool to a source file of the service (relative to the service dir)."""

    def __init__(self, service_dir: Path, sources: list[Path]):
        self.by_name: dict[str, list[str]] = defaultdict(list)
        for p in sources:
            r = p.resolve().relative_to(service_dir.resolve()).as_posix()
            self.by_name[Path(r).name].append(r)

    def __call__(self, reported: str) -> str | None:
        reported = reported.replace("\\", "/")
        cands = self.by_name.get(Path(reported).name, [])
        best, best_len = None, -1
        for c in cands:
            a, b = c.split("/"), reported.split("/")
            n = 0
            while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
                n += 1
            if n > best_len:
                best, best_len = c, n
        return best


def _shape(lines: dict[str, dict[int, int]], contexts: dict[str, dict[int, set[str]]] | None = None) -> dict:
    files = {}
    for file, hits in lines.items():
        ctx = (contexts or {}).get(file, {})
        files[file] = {"executed_lines": sorted(n for n, h in hits.items() if h > 0),
                       "missing_lines": sorted(n for n, h in hits.items() if h <= 0),
                       "contexts": {str(n): sorted(t) for n, t in sorted(ctx.items())}}
    return files


def read_jacoco(report: Path, resolve) -> tuple[dict, list[str]]:
    root = ET.parse(report).getroot()
    lines: dict[str, dict[int, int]] = defaultdict(dict)
    unmatched = []
    for package in root.iter("package"):
        pkg = package.get("name", "")
        for sf in package.findall("sourcefile"):
            target = resolve(f"{pkg}/{sf.get('name')}" if pkg else sf.get("name"))
            if target is None:
                unmatched.append(f"{pkg}/{sf.get('name')}")
                continue
            for line in sf.findall("line"):
                nr, ci, mi = int(line.get("nr")), int(line.get("ci", 0)), int(line.get("mi", 0))
                if ci or mi:
                    lines[target][nr] = max(lines[target].get(nr, 0), ci)
    return _shape(lines), unmatched


def read_cobertura(report: Path, resolve) -> tuple[dict, list[str]]:
    root = ET.parse(report).getroot()
    sources = [s.text.strip() for s in root.iter("source") if s.text]
    lines: dict[str, dict[int, int]] = defaultdict(dict)
    unmatched = []
    for cls in root.iter("class"):
        filename = cls.get("filename", "")
        target = resolve(filename) or next((resolve(f"{s}/{filename}") for s in sources if resolve(f"{s}/{filename}")), None)
        if target is None:
            unmatched.append(filename)
            continue
        for line in cls.iter("line"):
            nr, hits = int(line.get("number")), int(float(line.get("hits", 0)))
            lines[target][nr] = max(lines[target].get(nr, 0), hits)
    return _shape(lines), sorted(set(unmatched))


def read_lcov(report: Path, resolve) -> tuple[dict, list[str]]:
    lines: dict[str, dict[int, int]] = defaultdict(dict)
    contexts: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    unmatched, target, test = [], None, ""
    for raw in report.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("TN:"):
            test = raw[3:].strip()
        elif raw.startswith("SF:"):
            target = resolve(raw[3:].strip())
            if target is None:
                unmatched.append(raw[3:].strip())
        elif raw.startswith("DA:") and target:
            nr, hits = raw[3:].split(",")[:2]
            nr, hits = int(nr), int(float(hits))
            lines[target][nr] = max(lines[target].get(nr, 0), hits)
            if hits > 0 and test:
                contexts[target][nr].add(test)
        elif raw.startswith("end_of_record"):
            target = None
    return _shape(lines, contexts), unmatched


def read_go(report: Path, resolve) -> tuple[dict, list[str]]:
    lines: dict[str, dict[int, int]] = defaultdict(dict)
    unmatched = set()
    for raw in report.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(.+?):(\d+)\.\d+,(\d+)\.\d+ \d+ (\d+)$", raw)
        if not m:
            continue
        target = resolve(m.group(1))
        if target is None:
            unmatched.add(m.group(1))
            continue
        for nr in range(int(m.group(2)), int(m.group(3)) + 1):
            lines[target][nr] = max(lines[target].get(nr, 0), int(m.group(4)))
    return _shape(lines), sorted(unmatched)


def read_istanbul(report: Path, resolve) -> tuple[dict, list[str]]:
    data = json.loads(report.read_text(encoding="utf-8"))
    lines: dict[str, dict[int, int]] = defaultdict(dict)
    unmatched = []
    for path, cov in data.items():
        target = resolve(cov.get("path", path))
        if target is None:
            unmatched.append(path)
            continue
        for sid, loc in cov.get("statementMap", {}).items():
            hits = cov.get("s", {}).get(sid, 0)
            for nr in range(loc["start"]["line"], loc["end"]["line"] + 1):
                lines[target][nr] = max(lines[target].get(nr, 0), hits)
    return _shape(lines), unmatched


def read_coverage_py(report: Path, resolve) -> tuple[dict, list[str]]:
    data = json.loads(report.read_text(encoding="utf-8"))
    files, unmatched = {}, []
    for path, cov in data.get("files", {}).items():
        target = resolve(path) or path.replace("\\", "/")
        files[target] = cov
    return files, unmatched


READERS = {"jacoco": read_jacoco, "cobertura": read_cobertura, "lcov": read_lcov, "go": read_go,
           "istanbul": read_istanbul, "coverage-py": read_coverage_py}


def convert(fmt: str, report: Path, service_dir: Path, sources: list[Path]) -> dict:
    if fmt not in READERS:
        raise SystemExit(f"unknown coverage format {fmt!r}; choose from {', '.join(FORMATS)}")
    if not report.exists():
        raise FileNotFoundError(f"coverage report not found: {report}")
    files, unmatched = READERS[fmt](report, Resolver(service_dir, sources))
    per_test = any(f.get("contexts") for f in files.values())
    return {"meta": {"format": fmt, "report": report.as_posix(), "per_test": per_test,
                     "files": len(files), **({"unmatched": unmatched[:20]} if unmatched else {})},
            "files": files}


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    fmt, report, service_dir, out = argv
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from common import source_files
    base = Path(service_dir)
    data = convert(fmt, Path(report), base, source_files(base))
    Path(out).write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{fmt}: {data['meta']['files']} files, per_test={data['meta']['per_test']} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
