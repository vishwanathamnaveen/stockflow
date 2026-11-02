"""Discover an application's layout from its folder: services, shared library, languages, source folders, test
commands, coverage reports, API contracts, business-rule tables and QA test cases. Writes the service registry and
the `brownfield:` layout so the context tools can run; owners and descriptions stay TBD for a human.

    python tools/context/discover.py                 # print the plan for this repo (nothing written)
    python tools/context/discover.py --write         # write config/services.yaml + .claude/config.yaml layout
    python tools/context/discover.py --write --force # also replace an existing service registry
    python tools/context/discover.py --json          # the plan as JSON

The installer runs it on the target path, so a user only gives the application folder. Standard library only (runs
before `pip install`). It reads build files, never runs them, and never moves or edits product code.

What it recognises
  build units   Maven (pom.xml, <modules> aggregators), Gradle (settings.gradle include), npm / yarn / pnpm
                (package.json, workspaces), Go (go.mod), .NET (*.csproj; *Tests projects become the tests of the
                project they reference), Python (pyproject.toml / setup.py / setup.cfg, or a folder holding a package
                with __init__.py and a tests/ folder), Rust (Cargo.toml), PHP (composer.json), Ruby (Gemfile)
  containers    a unit whose source all lives in child units (a parent POM, a workspace root, a repo-level
                requirements.txt for tooling) is a container, not a service
  libraries     a unit other units depend on (Maven dependency, Gradle project(), npm workspace dependency,
                .NET ProjectReference) or named common / shared / core / lib(s) / commons / utils, with no entry point
                of its own -> the shared library (`common`); further libraries are registered as their own targets
  QA            folders of Gherkin features or JSON test cases (Zephyr / Xray shape) outside any unit ->
                brownfield.test_cases; a folder that is only QA is never a service
  rules         markdown tables `| BR-nn | rule | where |` -> brownfield.business_rules.files (+ id pattern)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

LANGUAGES = {".py": "python", ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".cs": "csharp", ".ts": "typescript",
             ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".go": "go",
             ".rb": "ruby", ".php": "php", ".rs": "rust", ".scala": "scala", ".swift": "swift", ".groovy": "groovy",
             ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp"}
SKIP = {".git", ".venv", "venv", ".venv-context", "node_modules", "target", "build", "dist", "out", "bin", "obj",
        ".gradle", ".mvn", "vendor", "__pycache__", "graphify-out", ".idea", ".vs", ".vscode", "coverage", ".next",
        ".nuxt", ".tox", ".pytest_cache", "site-packages", ".terraform", "TestResults"}
KIT = {"tools/context", ".claude", "artifacts", "graphs", "var", "knowledge", "docs/context-engine",
       "scripts/_paths.py", "scripts/graphify_all.py", "scripts/run_tests.py", "scripts/intake-safety-scan.py"}
LIB_NAMES = re.compile(r"^(common|commons|shared|share|core|lib|libs|library|utils?|sdk|base|platform-common|.*-common|"
                       r".*-shared|.*-lib|.*-core|.*\.common|.*\.shared|.*\.core)$", re.I)
ENTRY_POINTS = re.compile(r"@SpringBootApplication|public static void main\(|fun main\(|func main\(\)|"
                          r"FastAPI\(|Flask\(__name__\)|express\(\)|NestFactory\.create|WebApplication\.Create|"
                          r"Host\.CreateDefaultBuilder|uvicorn\.run|app\.listen\(|@QuarkusMain|Micronaut\.run")
# a real process entry point; an app *factory* (FastAPI(), express()) inside a shared package does not make it a service
MAIN_POINTS = re.compile(r"@SpringBootApplication|public static void main\(|fun main\(|func main\(\)|__name__\s*==\s*['\"]__main__|"
                         r"NestFactory\.create|WebApplication\.Create|@QuarkusMain|Micronaut\.run")
JACOCO_CLI = ("org.jacoco:jacoco-maven-plugin:0.8.12:prepare-agent test org.jacoco:jacoco-maven-plugin:0.8.12:report")


# --------------------------------------------------------------------------- walking


def _kit_path(rel: str) -> bool:
    return any(rel == k or rel.startswith(k + "/") for k in KIT)


def walk(root: Path, max_depth: int = 25):
    """Files under root, skipping build output, dependencies and the kit (depth-limited for huge monorepos)."""
    stack = [(root, 0)]
    while stack:
        folder, depth = stack.pop()
        try:
            entries = sorted(folder.iterdir())
        except (PermissionError, OSError):
            continue
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            if entry.name in SKIP or _kit_path(rel) or entry.name.startswith(".") and entry.is_dir():
                continue
            if entry.is_dir():
                if depth < max_depth:
                    stack.append((entry, depth + 1))
            else:
                yield entry


def _read(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


# --------------------------------------------------------------------------- build units


def _unit(root: Path, folder: Path, build: str, **extra) -> dict:
    rel = folder.relative_to(root).as_posix() if folder != root else "."
    return {"path": rel, "build": build, "folder": folder, **extra}


def find_units(root: Path, files: list[Path]) -> list[dict]:
    units: dict[str, dict] = {}
    by_dir: dict[Path, set[str]] = {}
    for f in files:
        by_dir.setdefault(f.parent, set()).add(f.name)
    for folder, names in sorted(by_dir.items(), key=lambda kv: len(kv[0].parts)):
        key = folder.as_posix()
        if "pom.xml" in names:
            pom = _read(folder / "pom.xml")
            modules = re.findall(r"<module>\s*([^<\s]+)\s*</module>", pom)
            artifact = _pom_artifact(pom)
            units[key] = _unit(root, folder, "maven", modules=modules, artifact=artifact,
                               deps=re.findall(r"<artifactId>\s*([^<\s]+)\s*</artifactId>", _strip_parent(pom)),
                               aggregator="<packaging>pom</packaging>" in pom.replace(" ", "") or bool(modules),
                               jacoco="jacoco-maven-plugin" in pom)
        elif names & {"build.gradle", "build.gradle.kts"} or names & {"settings.gradle", "settings.gradle.kts"}:
            settings = _read(folder / "settings.gradle") + _read(folder / "settings.gradle.kts")
            includes = [m.replace(":", "/").strip("/") for m in re.findall(r"""include\s*\(?\s*['"]([^'"]+)['"]""", settings)]
            build = _read(folder / "build.gradle") + _read(folder / "build.gradle.kts")
            units[key] = _unit(root, folder, "gradle", modules=includes, aggregator=bool(includes) and not (folder / "src").is_dir(),
                               deps=re.findall(r"""project\(\s*['"]:?([^'"]+)['"]\s*\)""", build),
                               artifact=folder.name, jacoco="jacoco" in build,
                               wrapper=(folder / "gradlew").exists())
        elif "package.json" in names:
            try:
                pkg = json.loads(_read(folder / "package.json") or "{}")
            except json.JSONDecodeError:
                pkg = {}
            ws = pkg.get("workspaces") or []
            ws = ws.get("packages", []) if isinstance(ws, dict) else ws
            deps = list((pkg.get("dependencies") or {}).keys()) + list((pkg.get("devDependencies") or {}).keys())
            units[key] = _unit(root, folder, "npm", modules=ws, artifact=pkg.get("name") or folder.name, deps=deps,
                               aggregator=bool(ws), test_script=(pkg.get("scripts") or {}).get("test", ""),
                               runner="vitest" if "vitest" in deps else "jest" if "jest" in deps or "ts-jest" in deps else None)
        elif "go.mod" in names:
            units[key] = _unit(root, folder, "go", artifact=(re.findall(r"^module\s+(\S+)", _read(folder / "go.mod"), re.M)
                                                             or [folder.name])[0])
        elif any(n.endswith(".csproj") for n in names):
            proj = next(n for n in sorted(names) if n.endswith(".csproj"))
            text = _read(folder / proj)
            refs = [Path(r.replace("\\", "/")).stem for r in re.findall(r'ProjectReference\s+Include="([^"]+)"', text)]
            is_test = bool(re.search(r"(xunit|nunit|MSTest|Microsoft\.NET\.Test\.Sdk)", text)) or Path(proj).stem.endswith(("Tests", "Test"))
            units[key] = _unit(root, folder, "dotnet", artifact=Path(proj).stem, deps=refs, test_project=is_test,
                               project_file=proj)
        elif names & {"pyproject.toml", "setup.py", "setup.cfg"}:
            units[key] = _unit(root, folder, "python", artifact=folder.name)
        elif "Cargo.toml" in names:
            units[key] = _unit(root, folder, "cargo", artifact=folder.name)
        elif "composer.json" in names:
            units[key] = _unit(root, folder, "composer", artifact=folder.name)
        elif "Gemfile" in names:
            units[key] = _unit(root, folder, "bundler", artifact=folder.name)
    # Python services without build files: <dir>/<pkg>/__init__.py next to <dir>/tests/ (a common plain layout)
    for folder, names in by_dir.items():
        if "__init__.py" in names and folder.parent.as_posix() not in units:
            parent = folder.parent
            if (parent / "__init__.py").exists():
                continue                                    # a sub-package, not the top package
            if (parent / "tests").is_dir() or (parent / "test").is_dir():
                units.setdefault(parent.as_posix(), _unit(root, parent, "python", artifact=parent.name,
                                                          package=folder.name))
    return list(units.values())


def _strip_parent(pom: str) -> str:
    return re.sub(r"<parent>.*?</parent>", "", re.sub(r"<build>.*", "", pom, flags=re.S), flags=re.S)


def _pom_artifact(pom: str) -> str | None:
    m = re.search(r"<artifactId>\s*([^<\s]+)\s*</artifactId>", _strip_parent(pom))
    return m.group(1) if m else None


# --------------------------------------------------------------------------- classification


def _languages(folder: Path, files: list[Path], nested: list[Path]) -> Counter:
    counts = Counter()
    for f in files:
        if f.suffix.lower() in LANGUAGES and folder in f.parents and not any(n in f.parents for n in nested):
            counts[LANGUAGES[f.suffix.lower()]] += 1
    return counts


def _is_test_path(rel: str) -> bool:
    return bool(re.search(r"(^|/)(tests?|__tests__|spec|src/test)(/|$)|Tests?\.(java|kt|cs)$|_test\.(go|py|rb)$|"
                          r"\.(test|spec)\.[jt]sx?$|(^|/)test_[^/]*\.py$", rel))


def classify(root: Path, units: list[dict], files: list[Path]) -> list[dict]:
    folders = {u["folder"] for u in units}
    for u in units:
        nested = [f for f in folders if f != u["folder"] and u["folder"] in f.parents]
        u["nested"] = nested
        u["languages"] = _languages(u["folder"], files, nested)
        own = [f for f in files if f.suffix.lower() in LANGUAGES and u["folder"] in f.parents
               and not any(n in f.parents for n in nested)]
        u["source_files"] = own
        u["product_files"] = [f for f in own if not _is_test_path(f.relative_to(root).as_posix())]
        texts = [_read(f, 60_000) for f in u["product_files"][:400]]
        u["entry_point"] = any(ENTRY_POINTS.search(t) for t in texts)
        u["main_point"] = any(MAIN_POINTS.search(t) for t in texts)
    # containers: source only in child units (parent POM, workspace root, tooling requirements.txt at the root)
    for u in units:
        u["container"] = bool(u["nested"]) and (u.get("aggregator") or len(u["product_files"]) == 0
                                                or (u["path"] == "." and u["build"] == "python"
                                                    and len(u["product_files"]) < 0.1 * sum(len(n["product_files"]) for n in units if n is not u)))
    live = [u for u in units if not u["container"] and u["product_files"] or u.get("test_project")]
    # .NET test projects belong to the project they reference
    for u in [u for u in live if u.get("test_project")]:
        owner = next((o for o in live if not o.get("test_project") and o["artifact"] in u.get("deps", [])), None)
        if owner:
            owner.setdefault("test_projects", []).append(u)
    live = [u for u in live if not u.get("test_project")]
    # Python has no dependency declarations between local packages: read the imports
    for u in live:
        if u["languages"].most_common(1) and u["languages"].most_common(1)[0][0] == "python":
            pkgs = {p.parent.name for p in u["folder"].glob("*/__init__.py")} | {p.parent.name for p in u["folder"].glob("src/*/__init__.py")}
            u["py_packages"] = pkgs
    for u in live:
        if u.get("py_packages") is not None:
            text = "\n".join(_read(f, 40_000) for f in u["source_files"][:300])
            u.setdefault("deps", [])
            u["deps"] = list(u["deps"]) + sorted({m for o in live if o is not u for m in o.get("py_packages", set())
                                                  if re.search(rf"^\s*(from|import)\s+{re.escape(m)}\b", text, re.M)})
    for u in live:
        dependents = [o for o in live if o is not u and (u.get("artifact") in o.get("deps", [])
                                                        or Path(u["path"]).name in o.get("deps", [])
                                                        or set(u.get("py_packages", ())) & set(o.get("deps", [])))]
        u["dependents"] = [o["path"] for o in dependents]
        u["kind"] = "library" if (dependents and not u["main_point"]) or (
            not u["entry_point"] and LIB_NAMES.match(Path(u["path"]).name or "")) else "service"
    return live


def source_folder(u: dict, root: Path) -> str | None:
    folder = u["folder"]
    lang = u["languages"].most_common(1)[0][0] if u["languages"] else None
    if u.get("package"):
        return u["package"]
    for cand in ({"java": ["src/main/java"], "kotlin": ["src/main/kotlin", "src/main/java"],
                  "scala": ["src/main/scala"], "groovy": ["src/main/groovy"]}.get(lang, [])):
        if (folder / cand).is_dir():
            return cand
    if lang == "python":
        pkgs = sorted(p.parent.name for p in folder.glob("*/__init__.py") if p.parent.name not in ("tests", "test"))
        src_pkgs = sorted(f"src/{p.parent.name}" for p in folder.glob("src/*/__init__.py"))
        found = pkgs or src_pkgs
        return found[0] if len(found) == 1 else None
    if lang in ("typescript", "javascript") and (folder / "src").is_dir():
        return "src"
    return None


def tests_for(u: dict, root: Path) -> dict:
    """Proposed test_command + coverage (the human confirms; the tool never runs builds during discovery)."""
    folder, lang = u["folder"], (u["languages"].most_common(1)[0][0] if u["languages"] else None)
    b = u["build"]
    if b == "maven":
        agg = _maven_root(u, root)
        mvn = "./mvnw" if (agg / "mvnw").exists() else "mvn"
        goals = "test jacoco:report" if u.get("jacoco") else JACOCO_CLI
        if agg != folder:
            module = folder.relative_to(agg).as_posix()
            cwd = Path(*[".."] * len(folder.relative_to(agg).parts)).as_posix()
            return {"test_command": f"{mvn} -q -B -pl {module} -am {goals}", "test_cwd": cwd,
                    "coverage": {"format": "jacoco", "path": "target/site/jacoco/jacoco.xml"},
                    "junit": "target/surefire-reports/*.xml"}
        return {"test_command": f"{mvn} -q -B {goals}", "coverage": {"format": "jacoco", "path": "target/site/jacoco/jacoco.xml"},
                "junit": "target/surefire-reports/*.xml"}
    if b == "gradle":
        g = "./gradlew" if u.get("wrapper") or (root / "gradlew").exists() else "gradle"
        out = {"test_command": f"{g} test" + (" jacocoTestReport" if u.get("jacoco") else ""), "junit": "build/test-results/test/*.xml"}
        if u.get("jacoco"):
            out["coverage"] = {"format": "jacoco", "path": "build/reports/jacoco/test/jacocoTestReport.xml"}
        else:
            out["gap"] = "no JaCoCo plugin in the Gradle build: tests run, coverage stays missing until it is applied"
        return out
    if b == "npm":
        if u.get("runner") == "vitest":
            return {"test_command": "npx vitest run --coverage --coverage.reporter=lcov", "coverage": {"format": "lcov", "path": "coverage/lcov.info"}}
        if u.get("runner") == "jest" or "jest" in (u.get("test_script") or ""):
            return {"test_command": "npx jest --coverage --coverageReporters=lcov", "coverage": {"format": "lcov", "path": "coverage/lcov.info"}}
        return {"test_command": "npm test", "gap": "test runner not recognised: add lcov coverage to the test command"}
    if b == "go":
        return {"test_command": "go test ./... -coverprofile=cover.out", "coverage": {"format": "go", "path": "cover.out"}}
    if b == "dotnet":
        tp = (u.get("test_projects") or [None])[0]
        if tp is None:
            return {"gap": "no test project references this project"}
        rel = Path(*[".."] * len(folder.relative_to(root).parts), tp["path"], tp["project_file"]).as_posix() \
            if u["path"] != "." else f"{tp['path']}/{tp['project_file']}"
        return {"test_command": f'dotnet test {rel} --collect:"XPlat Code Coverage" --results-directory TestResults',
                "coverage": {"format": "cobertura", "path": "TestResults/*/coverage.cobertura.xml"}}
    if lang == "python":
        if (folder / "tests").is_dir():
            return {}                                             # run_tests.py default: pytest --cov per test
        if (root / "tests").is_dir() and u["path"] != ".":
            return {"gap": "tests live outside the service folder: per-test coverage needs a test_command"}
        return {"gap": "no tests/ folder found"}
    if b == "cargo":
        return {"test_command": "cargo llvm-cov --lcov --output-path lcov.info", "coverage": {"format": "lcov", "path": "lcov.info"}}
    if b == "composer":
        return {"test_command": "vendor/bin/phpunit --coverage-cobertura=coverage.xml", "coverage": {"format": "cobertura", "path": "coverage.xml"}}
    if b == "bundler":
        return {"test_command": "bundle exec rspec", "gap": "add simplecov-lcov for coverage"}
    return {"gap": "no build tool recognised"}


def _maven_root(u: dict, root: Path) -> Path:
    """The outermost aggregator POM that lists this module (multi-module builds run from there)."""
    folder, best = u["folder"], u["folder"]
    for parent in folder.parents:
        if root not in parent.parents and parent != root:
            break
        pom = parent / "pom.xml"
        if pom.exists() and re.search(r"<module>", _read(pom)):
            best = parent
        if parent == root:
            break
    return best


# --------------------------------------------------------------------------- QA, rules, contracts


def find_test_cases(root: Path, files: list[Path], unit_folders: list[Path]) -> list[dict]:
    """Folders of Gherkin features or JSON test cases (outside the source trees of services)."""
    features, cases = Counter(), Counter()
    for f in files:
        if f.suffix == ".feature":
            features[f.parent] += 1
        elif f.suffix == ".json" and f.stat().st_size < 400_000:
            text = _read(f, 20_000)
            if re.search(r'"(testScript|steps|testSteps|precondition|objective)"', text) and \
                    re.search(r'"(key|testKey|name|summary)"', text):
                cases[f.parent] += 1
    out = []

    def top(counter: Counter) -> list[Path]:
        dirs = sorted(counter)
        roots = [d for d in dirs if not any(o in d.parents for o in dirs)]
        merged = []
        for r in roots:   # a folder of case sub-folders (testcases/<area>/*.json) is one source
            parent = r.parent
            siblings = [d for d in roots if d.parent == parent]
            pick = parent if len(siblings) > 1 and parent != root else r
            if pick not in merged:
                merged.append(pick)
        return merged

    for fmt, counter in (("zephyr-json", cases), ("gherkin", features)):
        for folder in top(counter):
            inside_source = any(u in folder.parents and (u / "src").is_dir() and "src" in folder.relative_to(u).parts
                                for u in unit_folders)
            if not inside_source:
                n = sum(c for d, c in counter.items() if d == folder or folder in d.parents)
                out.append({"path": folder.relative_to(root).as_posix(), "format": fmt, "files": n})
    return out


def find_rules(root: Path, files: list[Path]) -> tuple[list[str], str | None]:
    found, prefixes = [], Counter()
    for f in files:
        if f.suffix.lower() != ".md" or f.stat().st_size > 2_000_000:
            continue
        rows = re.findall(r"^\|\s*([A-Z]{2,5})-\d+\s*\|[^|\n]+\|[^|\n]+\|", _read(f), re.M)
        rows = [r for r in rows if r not in ("ADR", "FR", "NFR", "US")]
        if len(rows) >= 2:
            found.append(f.relative_to(root).as_posix())
            prefixes.update(rows)
    pattern = "|".join(f"{p}-\\d+" for p, _ in prefixes.most_common(2)) if prefixes else None
    return found, pattern


def find_openapi(folder: Path, files: list[Path], root: Path) -> str | None:
    for f in files:
        if folder in f.parents and re.match(r"^(openapi|swagger)[\w.-]*\.(json|ya?ml)$", f.name, re.I) \
                and "node_modules" not in f.parts:
            return f.relative_to(root).as_posix()
    return None


# --------------------------------------------------------------------------- plan


def _name(u: dict, taken: set[str]) -> str:
    base = Path(u["path"]).name if u["path"] != "." else (u.get("artifact") or "app")
    base = re.sub(r"[^a-z0-9-]+", "-", base.lower()).strip("-") or "app"
    base = re.sub(r"-(service|svc|api|app)$", "", base) or base
    name, i = base, 2
    while name in taken:
        name, i = f"{base}-{i}", i + 1
    taken.add(name)
    return name


def plan(root: Path) -> dict:
    root = root.resolve()
    files = list(walk(root))
    raw = find_units(root, files)
    units = classify(root, raw, files)
    libs = sorted((u for u in units if u["kind"] == "library"), key=lambda u: (-len(u["dependents"]), u["path"]))
    # the shared library: the one most depended on, else one named like a library (common, shared, core, ...)
    common = next((u for u in libs if u["dependents"]), None) or next(
        (u for u in libs if LIB_NAMES.match(Path(u["path"]).name or "")), None)
    services, taken = [], {"common", "overall"}     # reserved target names
    for u in sorted(units, key=lambda u: u["path"]):
        if u is common:
            continue
        lang = u["languages"].most_common(1)[0][0] if u["languages"] else None
        entry = {"name": _name(u, taken), "path": u["path"], "package": source_folder(u, root), "language": lang,
                 "languages": dict(u["languages"]), "build": u["build"], "kind": u["kind"],
                 "files": len(u["product_files"]), "tests": len(u["source_files"]) - len(u["product_files"]),
                 "openapi": find_openapi(u["folder"], files, root), **tests_for(u, root)}
        services.append(entry)
    qa = find_test_cases(root, files, [u["folder"] for u in units])
    rules, rule_pattern = find_rules(root, files)
    stray = Counter(LANGUAGES[f.suffix.lower()] for f in files if f.suffix.lower() in LANGUAGES
                    and not any(u["folder"] == f.parent or u["folder"] in f.parents for u in raw if not u.get("container")))
    out = {"root": root.as_posix(), "services": services, "test_cases": qa, "business_rules": rules,
           "business_rule_id_pattern": rule_pattern, "git": (root / ".git").exists(),
           "common": None if common is None else {"path": common["path"], "package": source_folder(common, root),
                                                  "used_by": common["dependents"]},
           "unassigned_source": dict(stray)}
    if not services and not common and stray:
        # no build file anywhere: the whole folder is one application
        lang = stray.most_common(1)[0][0]
        out["services"] = [{"name": _name({"path": ".", "artifact": root.name}, set()), "path": ".", "package": None,
                            "language": lang, "languages": dict(stray), "build": None, "kind": "service",
                            "files": sum(stray.values()), "tests": 0, "openapi": None,
                            "gap": "no build file: add test_command / coverage by hand"}]
    return out


# --------------------------------------------------------------------------- writing


def _q(value) -> str:
    if value is None:
        return "null"
    text = str(value)
    if re.match(r"^[\w./*{}@:+-]+$", text) and not re.match(r"^(true|false|null|yes|no|on|off|~|\d+)$", text, re.I):
        return text
    return "'" + text.replace("'", "''") + "'"


def services_yaml(p: dict) -> str:
    lines = [f"# Service registry drafted by tools/context/discover.py on {date.today().isoformat()} from the folder",
             "# layout and build files. A human confirms it: write each `description` (one business-language line, it",
             "# feeds the semantic search) and `owner` (TBD forces the guarded workflow), and check test_command.",
             "services:"]
    for s in p["services"]:
        lines.append(f"  {s['name']}:")
        lines.append(f"    path: {_q(s['path'])}")
        if s.get("package"):
            lines.append(f"    package: {_q(s['package'])}")
        lines.append("    owner: TBD")
        kind = "shared library" if s["kind"] == "library" else "service"
        lines.append(f"    description: TBD   # {kind}, {s['language'] or 'unknown language'}, {s['files']} source files, {s['tests']} test files")
        if s.get("test_command"):
            lines.append(f"    test_command: {_q(s['test_command'])}")
        if s.get("test_cwd"):
            lines.append(f"    test_cwd: {_q(s['test_cwd'])}")
        if s.get("coverage"):
            lines.append(f"    coverage: {{format: {s['coverage']['format']}, path: {_q(s['coverage']['path'])}}}")
        if s.get("junit"):
            lines.append(f"    junit: {_q(s['junit'])}")
        if s.get("openapi"):
            lines.append(f"    openapi: {_q(s['openapi'])}")
        if s.get("gap"):
            lines.append(f"    # gap: {s['gap']}")
    return "\n".join(lines) + "\n"


def patch_config(text: str, p: dict) -> str:
    """Set the discovered layout in .claude/config.yaml's brownfield block, keeping comments and other settings."""
    def setkey(text: str, key: str, value: str) -> str:
        return re.sub(rf"(?m)^(    {key}:)[^#\n]*?(\s*(#.*)?)$", lambda m: f"{m.group(1)} {value}{m.group(2)}", text, count=1)
    text = setkey(text, "services_root", '"."')
    common = p.get("common")
    text = setkey(text, "common_root", _q(common["path"]) if common else "null")
    text = setkey(text, "common_package", _q(common["package"]) if common and common.get("package") else "null")
    if p["business_rules"]:
        text = re.sub(r"(?m)^(    files:)\s*\[[^\]]*\]", lambda m: f"{m.group(1)} [{', '.join(_q(f) for f in p['business_rules'])}]",
                      text, count=1)
        if p.get("business_rule_id_pattern"):
            text = re.sub(r"(?m)^(    id_pattern:)\s*'[^']*'", lambda m: f"{m.group(1)} '{p['business_rule_id_pattern']}'", text, count=1)
    if p["test_cases"]:
        block = "".join(f"\n    - {{path: {_q(t['path'])}, format: {t['format']}}}" for t in p["test_cases"])
        text = re.sub(r"(?m)^  test_cases:\s*\[\][^\n]*", lambda m: "  test_cases:                          # discovered QA test cases" + block,
                      text, count=1)
    return text


def report(p: dict) -> str:
    out = [f"Layout of {p['root']}" + ("" if p["git"] else "   (no git: fine; history is unavailable)")]
    out.append(f"{'service':<22} {'path':<34} {'language':<11} {'build':<8} {'source':<20} tests")
    for s in p["services"]:
        out.append(f"{s['name']:<22} {s['path']:<34} {str(s['language']):<11} {str(s['build']):<8} "
                   f"{str(s.get('package') or '.'):<20} {s.get('test_command', '(pytest default)' if s['language'] == 'python' and not s.get('gap') else '-')}"
                   + (f"   [{s['kind']}]" if s["kind"] != "service" else ""))
        if s.get("gap"):
            out.append(f"{'':<22} gap: {s['gap']}")
    if p["common"]:
        out.append(f"shared library: {p['common']['path']} (source {p['common']['package'] or '.'}, used by "
                   f"{', '.join(p['common']['used_by']) or '-'})")
    for t in p["test_cases"]:
        out.append(f"QA test cases: {t['path']} ({t['format']}, {t['files']} files)")
    if p["business_rules"]:
        out.append(f"business rules: {', '.join(p['business_rules'])} (ids {p['business_rule_id_pattern']})")
    if p["unassigned_source"]:
        out.append(f"source outside any build unit (not graphed): {p['unassigned_source']}")
    if not p["services"]:
        out.append("no services found: describe the layout by hand in config/services.yaml (docs: LAYOUT-RECIPES.md)")
    return "\n".join(out)


def write(root: Path, p: dict, force: bool = False) -> list[str]:
    written = []
    reg = root / "config" / "services.yaml"
    existing = _read(reg) if reg.exists() else ""
    empty = not re.search(r"(?m)^  [A-Za-z0-9_-]+:\s*$", existing)
    if p["services"] and (force or empty):
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(services_yaml(p), encoding="utf-8")
        written.append("config/services.yaml")
    cfg = root / ".claude" / "config.yaml"
    if cfg.exists() and "brownfield:" in _read(cfg):
        text = _read(cfg)
        new = patch_config(text, p)
        if new != text:
            cfg.write_text(new, encoding="utf-8")
            written.append(".claude/config.yaml (brownfield layout, business rules, test cases)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--write", action="store_true", help="write config/services.yaml + the brownfield layout")
    parser.add_argument("--force", action="store_true", help="replace a service registry that already has services")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    p = plan(root)
    if args.json:
        print(json.dumps(p, indent=2, default=str))
    else:
        print(report(p))
    if args.write:
        done = write(root, p, args.force)
        print("\nwritten: " + (", ".join(done) or "nothing (registry already has services: --force replaces it)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
