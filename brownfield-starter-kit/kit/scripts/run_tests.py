"""Run each service's tests in its own process and write quality evidence.

    python scripts/run_tests.py                  # all suites
    python scripts/run_tests.py orders billing

Per service (config/services.yaml):

    orders:
      test_command: "mvn -q -B test jacoco:report"     # any shell command, run from the service folder, or from
      test_cwd: ".."                                   # `test_cwd` (relative to it: e.g. a multi-module root)
      coverage: {format: jacoco, path: target/site/jacoco/jacoco.xml}   # report path relative to the service folder
      junit: "target/surefire-reports/*.xml"           # optional: test results to collect

Without `test_command`, a Python service runs `pytest tests --cov=<package> --cov-context=test` (per-test coverage);
any other service is skipped with a suggested command, never a guessed one.

Outputs (inputs for the quality/test graph):
  var/quality/<suite>-junit.xml     test results (when the runner writes JUnit XML)
  var/quality/<suite>-coverage.json line coverage, per test where the format records it
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from _paths import COMMON, ROOT, common_package, has_common, registry, service_dir

sys.path.insert(0, str(ROOT / "tools" / "context"))
import coverage_formats  # noqa: E402
from common import language_of, service_excludes, source_files  # noqa: E402

QUALITY = ROOT / "var" / "quality"

SUGGESTIONS = [   # (marker file, suggested test_command, coverage format, report path)
    ("pom.xml", "mvn -q -B test jacoco:report", "jacoco", "target/site/jacoco/jacoco.xml"),
    ("build.gradle", "./gradlew test jacocoTestReport", "jacoco", "build/reports/jacoco/test/jacocoTestReport.xml"),
    ("build.gradle.kts", "./gradlew test jacocoTestReport", "jacoco", "build/reports/jacoco/test/jacocoTestReport.xml"),
    ("package.json", "npx jest --coverage --coverageReporters=lcov", "lcov", "coverage/lcov.info"),
    ("go.mod", "go test ./... -coverprofile=cover.out", "go", "cover.out"),
    ("*.csproj", 'dotnet test --collect:"XPlat Code Coverage" --results-directory TestResults', "cobertura",
     "TestResults/*/coverage.cobertura.xml"),
    ("*.sln", 'dotnet test --collect:"XPlat Code Coverage" --results-directory TestResults', "cobertura",
     "TestResults/*/coverage.cobertura.xml"),
    ("Gemfile", "bundle exec rspec  # with simplecov-lcov", "lcov", "coverage/lcov/*.lcov"),
    ("composer.json", "vendor/bin/phpunit --coverage-cobertura=coverage.xml", "cobertura", "coverage.xml"),
    ("Cargo.toml", "cargo llvm-cov --lcov --output-path lcov.info", "lcov", "lcov.info"),
]


def suites() -> dict[str, dict]:
    found = {"common": {"dir": COMMON, "package": common_package(), "cfg": {}}} if has_common() else {}
    for name, cfg in registry().items():
        found[name] = {"dir": service_dir(name), "package": cfg.get("package"), "cfg": cfg}
    return found


def is_python(name: str, directory: Path) -> bool:
    files = source_files(directory, exclude=service_excludes(name))
    return bool(files) and all(language_of(p) == "python" for p in files)


def suggestion(directory: Path) -> str:
    for marker, cmd, fmt, path in SUGGESTIONS:
        if list(directory.glob(marker)):
            return f'test_command: "{cmd}"  coverage: {{format: {fmt}, path: {path}}}'
    return "test_command: <your test command>  coverage: {format: <jacoco|cobertura|lcov|go|istanbul>, path: <report>}"


def run_pytest(name: str, directory: Path, package: str | None) -> bool:
    env = os.environ.copy()
    # the package's parent: the service folder, or e.g. <service>/src for `package: src/<pkg>`
    package = package or "."
    import_root = str((directory / package).parent)
    paths = [str(COMMON)] if has_common() else []
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths + [import_root, str(directory)]))
    env["COVERAGE_FILE"] = str(QUALITY / f".coverage-{name}")
    cmd = [
        sys.executable, "-m", "pytest", "tests", "-q",
        f"--rootdir={ROOT}", f"-c={ROOT / 'pytest.ini'}",
        f"--cov={package}", f"--cov-config={ROOT / '.coveragerc'}", "--cov-context=test",
        f"--cov-report=json:{QUALITY / f'{name}-coverage.json'}", "--cov-report=term:skip-covered",
        f"--junitxml={QUALITY / f'{name}-junit.xml'}",
    ]
    return subprocess.call(cmd, cwd=directory, env=env) == 0


def collect_junit(name: str, directory: Path, pattern: str | None, since: float = 0.0) -> None:
    if not pattern:
        return
    files = sorted(f for f in glob.glob(str(directory / pattern), recursive=True) if os.path.getmtime(f) >= since)
    if not files:
        return
    if len(files) == 1:
        shutil.copyfile(files[0], QUALITY / f"{name}-junit.xml")
        return
    import xml.etree.ElementTree as ET
    merged = ET.Element("testsuites")
    for f in files:
        root = ET.parse(f).getroot()
        merged.extend(list(root) if root.tag == "testsuites" else [root])
    ET.ElementTree(merged).write(QUALITY / f"{name}-junit.xml", encoding="utf-8", xml_declaration=True)


def run_command(name: str, directory: Path, cfg: dict) -> bool:
    cwd = directory / cfg["test_cwd"] if cfg.get("test_cwd") else directory
    started = time.time() - 2           # filesystem timestamp granularity
    ok = subprocess.call(cfg["test_command"], cwd=cwd, shell=True) == 0
    collect_junit(name, directory, cfg.get("junit"), since=started)   # paths are relative to the service folder
    cov = cfg.get("coverage") or {}
    if cov.get("format") and cov.get("path"):
        reports = sorted(glob.glob(str(directory / cov["path"]), recursive=True), key=os.path.getmtime)
        fresh = [r for r in reports if os.path.getmtime(r) >= started]
        if not fresh:
            # a report left by an earlier run is not evidence for this code: the old file is kept out
            print(f"  no coverage report written by this run at {cov['path']} (format {cov['format']})"
                  + (" - an older one exists and was ignored" if reports else "") + "; coverage not updated")
            (QUALITY / f"{name}-coverage.json").unlink(missing_ok=True)
            return False
        reports = fresh
        data = coverage_formats.convert(cov["format"], Path(reports[-1]), directory,
                                        source_files(directory, exclude=service_excludes(name)))
        (QUALITY / f"{name}-coverage.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
        print(f"  coverage: {data['meta']['files']} files ({cov['format']}, per-test={data['meta']['per_test']})"
              + (f"; unmatched report paths: {data['meta']['unmatched'][:3]}" if data["meta"].get("unmatched") else ""))
    return ok


def main(argv: list[str]) -> int:
    selected = suites()
    if argv:
        selected = {k: v for k, v in selected.items() if k in argv}
    QUALITY.mkdir(parents=True, exist_ok=True)
    failed, skipped = [], []
    for name, suite in selected.items():
        directory, cfg = Path(suite["dir"]), suite["cfg"]
        print(f"\n=== {name} ===", flush=True)
        if cfg.get("test_command"):
            ok = run_command(name, directory, cfg)
        elif is_python(name, directory) or (directory / "tests").is_dir() and any((directory / "tests").rglob("*.py")):
            ok = run_pytest(name, directory, suite["package"])
        else:
            print(f"  skipped: no test_command for {name} in config/services.yaml. Suggested: {suggestion(directory)}")
            skipped.append(name)
            continue
        if not ok:
            failed.append(name)
    if skipped:
        print("\nSKIPPED (no test_command): " + ", ".join(skipped))
    print("\nFAILED: " + ", ".join(failed) if failed else "\nall suites passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
