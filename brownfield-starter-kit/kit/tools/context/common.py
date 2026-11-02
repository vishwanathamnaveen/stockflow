"""Shared helpers for the brownfield context tools (paths, config, git, symbol index).

The tools are written in Python; the code they analyse can be in any language. Source files are read by a language
adapter (tools/context/lang_python.py for .py, tools/context/lang_treesitter.py for Java, Kotlin, C#, TypeScript,
JavaScript, Go, Ruby, PHP, Rust, Scala, Swift, Groovy, C and C++), and framework idioms (routes, events, clients,
tables) by tools/context/conventions.py. Everything downstream reads the neutral `Symbol` facts below.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from fnmatch import fnmatch, fnmatchcase
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _layout() -> dict:
    """`brownfield.layout` of .claude/config.yaml: where services and the optional shared library live."""
    path = ROOT / ".claude" / "config.yaml"
    cfg = ((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("brownfield") or {}) if path.exists() else {}
    return {"services_root": "services", "common_root": "libs/common", "common_package": None, **(cfg.get("layout") or {})}


LAYOUT = _layout()
SERVICES = ROOT / LAYOUT["services_root"]
# Shared library graphed as the extra target "common"; brownfield.layout.common_root: null when the repo has none.
COMMON = ROOT / LAYOUT["common_root"] if LAYOUT["common_root"] else None
GRAPHS = ROOT / "graphs"
CHANGES = ROOT / "artifacts" / "changes"
MEMORY = ROOT / "artifacts" / "memory" / "episodes.jsonl"
QUALITY = ROOT / "var" / "quality"
TRACES = ROOT / "var" / "traces"
LOCAL_STATE = ROOT / "var" / "context"          # refresh lock + last snapshot (local, git-ignored)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


@lru_cache
def registry() -> dict[str, dict]:
    """config/services.yaml `services:`. Per service: `path` (default <services_root>/<name>), `package` (source
    folder inside it, optional), `owner`, `description`, and optionally `port`, `tests`, `test_command`, `coverage`,
    `conventions`, `exclude` (see docs/context-engine/starter-kit/LAYOUT-RECIPES.md)."""
    return load_yaml(ROOT / "config" / "services.yaml")["services"]


@lru_cache
def brownfield_config() -> dict:
    """`brownfield:` block of .claude/config.yaml, with defaults when absent."""
    defaults = {
        "enabled_services": [],
        "confidence": {"execute": 0.80, "plan": 0.60},
        "risk_levels": {"low": 2, "medium": 6, "high": 10},
        "transitive_depth": 3,
    }
    path = ROOT / ".claude" / "config.yaml"
    if path.exists():
        defaults.update(load_yaml(path).get("brownfield") or {})
    return defaults


# Bump when the extraction/enrichment output shape changes: graphs built by an older version read as stale,
# so a tool upgrade forces a rebuild even when no source file changed (feedback #8 — version the artifacts).
# v3: enrichment stamps normalised source hashes + the non-code inputs it read (business rules, coverage, publishes).
# v4: language adapters (any language) + convention presets; symbols carry language and route.
CONTEXT_ENGINE_VERSION = 4


def build_config() -> dict:
    """The config that changes what the graphs/index contain. Stamped into artifacts; freshness compares it."""
    cfg = brownfield_config()
    conventions_file = ROOT / "config" / "conventions.yaml"
    return {
        "context_engine_version": CONTEXT_ENGINE_VERSION,
        "embedding_model": (cfg.get("semantic") or {}).get("model", "BAAI/bge-small-en-v1.5"),
        "transitive_depth": cfg.get("transitive_depth", 3),
        "knowledge_exclude": sorted(cfg.get("knowledge_exclude") or DEFAULT_KNOWLEDGE_EXCLUDE),
        "test_patterns": test_patterns(),
        "conventions": {s: c.get("conventions", "auto") for s, c in sorted(registry().items())}
        if (ROOT / "config" / "services.yaml").exists() else {},
        "custom_conventions": normalized_md5(conventions_file)[:12] if conventions_file.exists() else None,
    }


def build_config_hash() -> str:
    return hashlib.sha1(json.dumps(build_config(), sort_keys=True).encode("utf-8")).hexdigest()[:12]


DEFAULT_KNOWLEDGE_EXCLUDE = ["docs/context-engine/*", "docs/harness/*"]


def knowledge_excluded(path: Path) -> bool:
    """True for docs that describe the tooling, samples or presenter material (brownfield.knowledge_exclude)."""
    patterns = brownfield_config().get("knowledge_exclude") or DEFAULT_KNOWLEDGE_EXCLUDE
    return any(fnmatch(rel(path), p) for p in patterns)


def has_common() -> bool:
    return COMMON is not None and COMMON.is_dir()


def code_targets() -> list[str]:
    """Every per-target code graph: the registered services plus "common" when the repo has a shared library."""
    return list(registry()) + (["common"] if has_common() else [])


def common_package() -> str:
    """Source folder of the shared library: brownfield.layout.common_package, else its only Python package, else
    the library folder itself (non-Python libraries have no package marker)."""
    if LAYOUT.get("common_package"):
        return LAYOUT["common_package"]
    found = sorted(p.parent.name for p in COMMON.glob("*/__init__.py")) if has_common() else []
    if len(found) > 1:
        raise SystemExit(f"set brownfield.layout.common_package in .claude/config.yaml (found under "
                         f"{LAYOUT['common_root']}: {found})")
    if not found and has_common() and any(COMMON.glob("*.py")):
        raise SystemExit(f"set brownfield.layout.common_package in .claude/config.yaml (no package under "
                         f"{LAYOUT['common_root']})")
    return found[0] if found else "."


def service_dir(name: str) -> Path:
    if name == "common":
        return COMMON
    cfg = registry().get(name) or {}
    return (ROOT / cfg["path"]).resolve() if cfg.get("path") else SERVICES / name


def package_dir(name: str) -> Path:
    """The service's source folder: <service>/<package> (Python import package, `src/main/java`, `src`, ...), or
    the service folder itself when no package is registered."""
    if name == "common":
        return COMMON / common_package()
    package = (registry().get(name) or {}).get("package")
    return service_dir(name) / package if package else service_dir(name)


def service_prefix(name: str) -> str:
    """Repo-relative path prefix of a service's files: "services/orders/", or "" for a service at the repo root."""
    base = rel(service_dir(name))
    return "" if base in ("", ".") else base + "/"


def in_service(file: str, name: str) -> bool:
    prefix = service_prefix(name)
    return file.startswith(prefix) if prefix else not any(
        file.startswith(service_prefix(o)) for o in code_targets() if o != name and service_prefix(o))


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else ""


@lru_cache
def has_git() -> bool:
    """git is optional: freshness is content-based everywhere. Without it there is no change history and no commit
    stamp, and the files a change touched come from content snapshots (artifacts/changes/<id>/baseline.json)."""
    return git("rev-parse", "--is-inside-work-tree") == "true"


def head_commit() -> str:
    return git("rev-parse", "--short", "HEAD") if has_git() else ""


# --------------------------------------------------------------------------- source files


# build output, dependencies and tool state in any ecosystem: never source
SKIP_PARTS = {"graphify-out", "__pycache__", ".venv", "venv", ".pytest_cache", "node_modules", "target", "build",
              "dist", "out", "bin", "obj", ".gradle", ".mvn", ".idea", ".vs", ".vscode", "vendor", ".git", ".tox",
              "coverage", ".next", ".nuxt", ".terraform", ".dart_tool", "Pods", ".angular", ".svelte-kit"}
# the kit's own files and the artifacts it writes: never part of a service, even a service at the repo root
KIT_PARTS = ["tools/context", ".claude", "artifacts", "graphs", "var", "docs/context-engine", "knowledge",
             "scripts/_paths.py", "scripts/graphify_all.py", "scripts/run_tests.py", "scripts/intake-safety-scan.py"]


def _adapters():
    import lang_python
    import lang_treesitter
    return lang_python, lang_treesitter


def source_extensions() -> set[str]:
    _, ts = _adapters()
    return {".py"} | set(ts.EXTENSIONS)


def language_of(path: Path | str) -> str | None:
    if Path(path).suffix.lower() == ".py":
        return "python"
    _, ts = _adapters()
    return ts.language_of(path)


def _excluded(path: Path, base: Path, extra: list[str]) -> bool:
    if SKIP_PARTS & set(path.relative_to(base).parts):
        return True
    r = rel(path)
    if any(r == k or r.startswith(k + "/") for k in KIT_PARTS):
        return True
    return any(fnmatchcase(r, pattern) for pattern in extra)


def source_files(base: Path, *, exclude: list[str] | None = None) -> list[Path]:
    """Every source file an adapter can read under `base`, minus build output, the kit and `exclude` globs."""
    if base is None or not base.is_dir():
        return []
    exts = source_extensions()
    nested = [service_dir(o) for o in code_targets() if service_dir(o) is not None]
    nested = [n for n in nested if n != base and base in n.parents]   # services inside a root-level service
    out = []
    for p in sorted(base.rglob("*")):
        if p.suffix.lower() in exts and p.is_file() and not _excluded(p, base, exclude or []) \
                and not any(n in p.parents for n in nested):
            out.append(p)
    return out


def service_excludes(name: str) -> list[str]:
    cfg = {} if name == "common" else (registry().get(name) or {})
    return list(cfg.get("exclude") or []) + list((brownfield_config().get("layout") or {}).get("exclude") or [])


# --------------------------------------------------------------------------- tests


DEFAULT_TEST_PATTERNS = [
    "*/tests/*", "*/test/*", "*/__tests__/*", "*/spec/*", "*/testing/*", "*/src/test/*", "*/src/androidTest/*",
    "*/test_*.py", "*_test.py", "*Test.java", "*Tests.java", "*IT.java", "*Test.kt", "*Tests.kt", "*Spec.groovy",
    "*Test.groovy", "*Tests.cs", "*Test.cs", "*.Tests/*", "*.Test/*", "*_test.go", "*.test.ts", "*.test.tsx",
    "*.test.js", "*.test.jsx", "*.spec.ts", "*.spec.tsx", "*.spec.js", "*.spec.jsx", "*_spec.rb", "*_test.rb",
    "*Test.php", "*Spec.scala", "*Test.scala", "*Tests.swift",
]


def test_patterns() -> list[str]:
    """brownfield.tests.patterns (globs over "/" + repo-relative path); defaults cover the common ecosystems."""
    return list(((brownfield_config().get("tests") or {}).get("patterns")) or DEFAULT_TEST_PATTERNS)


@lru_cache(maxsize=None)
def is_test_path(path: str) -> bool:
    """Case-sensitive on every OS (fnmatch folds case on Windows: `*IT.java` would match BusinessUnit.java)."""
    probe = "/" + path.replace("\\", "/").lstrip("/")
    return any(fnmatchcase(probe, p) for p in test_patterns())


# --------------------------------------------------------------------------- content hashes / source state


def normalized_md5(path: Path) -> str:
    """MD5 of a text file with CRLF folded to LF, so a Windows working tree (autocrlf) and a Linux CI checkout of the
    same commit hash alike. graphify's own manifest.json hashes raw bytes and is not portable."""
    return hashlib.md5(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def data_digest(value) -> str:
    """Stable hash of JSON-able data (parsed inputs, so formatting-only edits do not count)."""
    return hashlib.sha1(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def files_digest(paths) -> str:
    return data_digest(sorted((rel(p), normalized_md5(p)) for p in paths if p.is_file()))


def source_hashes(base: Path) -> dict[str, str]:
    """Normalised hash of every source file under a service/lib dir, keyed relative to it (what the code graph is
    built from)."""
    name = next((t for t in code_targets() if service_dir(t) is not None and service_dir(t).resolve() == base.resolve()), None)
    excludes = service_excludes(name) if name else []
    return {p.relative_to(base).as_posix(): normalized_md5(p) for p in source_files(base, exclude=excludes)}


# Everything any context artifact is built from. Traces are left out on purpose: runtime evidence only ever proves
# presence, so new traffic refreshes it opportunistically but never makes the intelligence "stale".
SOURCE_STATE_FIXED = ["contracts", "config", "docs", "README.md", ".claude/config.yaml", "var/quality"]
SOURCE_STATE_SUFFIXES = {".py", ".json", ".yaml", ".yml", ".md", ".xml", ".properties", ".gradle", ".toml",
                         ".feature", ".csv", ".sql"}


def source_state_paths() -> list[str]:
    paths = list(SOURCE_STATE_FIXED)
    for target in code_targets():
        d = service_dir(target)
        if d is not None:
            r = rel(d)
            paths.append("." if r in ("", ".") else r)
    paths += [s["path"] for s in test_case_sources()]
    return list(dict.fromkeys(paths))


SOURCE_STATE_PATHS = SOURCE_STATE_FIXED   # kept for callers that read the constant; see source_state_paths()

# Document knowledge base (tools/context/knowledge_base.py): PDFs, spreadsheets and notes dropped under these roots.
KB_SUFFIXES = {".pdf", ".xlsx", ".xlsm", ".csv", ".md", ".txt"}
KB_BINARY_SUFFIXES = {".pdf", ".xlsx", ".xlsm"}


def kb_roots() -> list[Path]:
    return [ROOT / r for r in ((brownfield_config().get("knowledge_base") or {}).get("roots") or ["knowledge"])]


def file_digest(path: Path) -> str:
    """Raw bytes for binary documents (a CRLF fold would corrupt nothing but means nothing either); normalised text otherwise."""
    return hashlib.md5(path.read_bytes()).hexdigest() if path.suffix.lower() in KB_BINARY_SUFFIXES else normalized_md5(path)


def _state_excluded(p: Path) -> bool:
    r = rel(p)
    if SKIP_PARTS & set(Path(r).parts):
        return True
    # var/quality and .claude/config.yaml are inputs; the rest of var/, .claude/ and the kit's outputs are not
    if r.startswith("var/quality/") or r == ".claude/config.yaml":
        return False
    return any(r == k or r.startswith(k + "/") for k in KIT_PARTS)


def source_state_files() -> dict[str, str]:
    files = {}
    suffixes = SOURCE_STATE_SUFFIXES | source_extensions()
    for entry in source_state_paths():
        path = (ROOT / entry).resolve()
        candidates = [path] if path.is_file() else sorted(path.rglob("*")) if path.is_dir() else []
        for p in candidates:
            if p.is_file() and p.suffix.lower() in suffixes and not _state_excluded(p):
                files[rel(p)] = normalized_md5(p)
    for root in kb_roots():
        for p in sorted(root.rglob("*")) if root.is_dir() else []:
            if p.is_file() and p.suffix.lower() in KB_SUFFIXES:
                files[rel(p)] = file_digest(p)
    return files


def source_state(files: dict[str, str] | None = None) -> dict:
    """Identity of the inputs an artifact was built from. Before a commit exists there is no SHA to stamp, so record
    the base commit, whether the working tree differs from it, and a digest of the captured inputs."""
    files = source_state_files() if files is None else files
    if not has_git():   # no version control: the digest alone identifies the inputs
        return {"source_state_digest": data_digest(files), "base_commit": "", "working_tree": None}
    tracked = [p for p in source_state_paths() if not p.startswith("var/") and not p.startswith("..")]
    dirty = git("status", "--porcelain", "--", *tracked, ":(exclude)artifacts", ":(exclude)graphs", ":(exclude)var",
                ":(exclude)graphify-out", ":(exclude,glob)**/graphify-out/**")
    return {"source_state_digest": data_digest(files), "base_commit": head_commit(), "working_tree": bool(dirty)}


def product_files() -> dict[str, str]:
    """Normalised hash of every product file a change can touch: each code target's source and tests, contracts,
    config and business-rule files. Written as a change's baseline; diffed to find what the change touched (no git)."""
    out = {}
    for target in code_targets():
        base = service_dir(target)
        for p in source_files(base, exclude=service_excludes(target)):
            out[rel(p)] = normalized_md5(p)
    for entry in ["contracts", "config"]:
        root = ROOT / entry
        for p in sorted(root.rglob("*")) if root.is_dir() else []:
            if p.is_file() and not SKIP_PARTS & set(p.relative_to(ROOT).parts):
                out[rel(p)] = normalized_md5(p)
    for p in business_rule_files():
        if p.exists():
            out[rel(p)] = normalized_md5(p)
    return out


# --------------------------------------------------------------------------- safe writes / refresh lock


def write_atomic(path: Path, data: str | bytes) -> None:
    """Write to a sibling temp file, then os.replace: readers see the old file or the new one, never half of one.
    Retries the replace because Windows refuses it while a scanner (DLP/AV) briefly holds the target open."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    for attempt in range(10):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 9:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(0.2 * (attempt + 1))


LOCK_PATH = LOCAL_STATE / "refresh.lock"
LOCK_STALE_SECONDS = 30 * 60   # a refresh takes 45 s idle, ~5 min under a DLP scanner; older locks are abandoned


class RefreshLocked(RuntimeError):
    pass


def _lock_age(path: Path) -> float | None:
    try:
        return time.time() - path.stat().st_mtime
    except FileNotFoundError:
        return None


def refresh_in_progress() -> bool:
    age = _lock_age(LOCK_PATH)
    return age is not None and age < LOCK_STALE_SECONDS


@contextmanager
def refresh_lock():
    """One writer at a time for graphs + index. An abandoned lock (crashed refresh) is taken over after 30 minutes."""
    path = LOCK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    age = _lock_age(path)
    if age is not None and age >= LOCK_STALE_SECONDS:
        print(f"warning: taking over an abandoned refresh lock ({int(age)} s old): {rel(path)}")
        path.unlink(missing_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else "?"
        raise RefreshLocked(f"another refresh is running ({holder}); lock {rel(path)}") from None
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"pid {os.getpid()} since {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def openapi_path_regex(path: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\\\{[^}]+\\\}", r"[^/]+", re.escape(path)) + "$")


def openapi_file(service: str) -> Path | None:
    """contracts/openapi/<service>.json|yaml|yml (the first that exists), or the service's `openapi:` path."""
    cfg = registry().get(service) or {}
    if cfg.get("openapi"):
        path = ROOT / cfg["openapi"]
        return path if path.exists() else None
    for suffix in (".json", ".yaml", ".yml"):
        path = ROOT / "contracts" / "openapi" / f"{service}{suffix}"
        if path.exists():
            return path
    return None


def load_openapi(path: Path) -> dict:
    return load_json(path) if path.suffix == ".json" else load_yaml(path)


# --------------------------------------------------------------------------- business rules


def business_rule_files() -> list[Path]:
    """brownfield.business_rules.files (default docs/business-rules.md): markdown tables `| BR-nnn | rule | where |`."""
    cfg = brownfield_config().get("business_rules") or {}
    return [ROOT / f for f in (cfg.get("files") or ["docs/business-rules.md"])]


def business_rule_id_pattern() -> str:
    return (brownfield_config().get("business_rules") or {}).get("id_pattern") or r"BR-\d+"


def is_business_rule_file(path: Path) -> bool:
    return path.resolve() in {p.resolve() for p in business_rule_files()}


def doc_paths() -> list[Path]:
    """Markdown the manifest searches for references: docs/ (brownfield.docs.roots) plus each service's own docs/
    and README.md."""
    roots = [ROOT / r for r in ((brownfield_config().get("docs") or {}).get("roots") or ["docs"])]
    out = [p for r in roots if r.is_dir() for p in r.rglob("*.md")]
    for service in registry():
        base = service_dir(service)
        if base != ROOT:
            out += sorted((base / "docs").rglob("*.md")) if (base / "docs").is_dir() else []
            out += [base / "README.md"] if (base / "README.md").exists() else []
    return out


# --------------------------------------------------------------------------- test-case sources (QA repositories)


def test_case_sources() -> list[dict]:
    """brownfield.test_cases: [{path, format}] — external test cases (Zephyr / Xray JSON, Gherkin, CSV) linked to
    code by their `Covers` field or step text (tools/context/test_cases.py)."""
    out = []
    for entry in brownfield_config().get("test_cases") or []:
        if isinstance(entry, str):
            entry = {"path": entry}
        out.append({"format": "auto", **entry})
    return out


# --------------------------------------------------------------------------- symbol index


_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def split_words(identifier: str) -> list[str]:
    """snake_case, camelCase, PascalCase, kebab-case -> lower-case words."""
    return [w.lower() for w in re.split(r"[_\-\s.]+", _CAMEL.sub("_", identifier)) if w]


@dataclass
class Symbol:
    service: str
    file: str            # repo-relative
    qualname: str        # e.g. "update_order", "BillingClient.get_invoice", "OrderServiceImpl.approve"
    kind: str            # function | class | method
    start: int
    end: int
    refs: set[str] = field(default_factory=set)       # identifiers referenced in the body
    strings: set[str] = field(default_factory=set)    # string constants (topics, dict keys, flags)
    decorators: list[str] = field(default_factory=list)
    signature: str = ""                               # "def f(a: int) -> Out" / "public Order place(Long id)"
    docstring: str = ""
    bases: list[str] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)   # class attributes: name -> type
    language: str = "python"
    route: tuple[str, str] | None = None              # (METHOD, path), set by the service's conventions

    @property
    def name(self) -> str:
        return self.qualname.rsplit(".", 1)[-1]

    @property
    def module(self) -> str:
        return Path(self.file).stem

    @property
    def key(self) -> str:
        return f"{self.service}:{self.file}::{self.qualname}"

    @property
    def is_test(self) -> bool:
        return is_test_path(self.file)

    @property
    def words(self) -> list[str]:
        """Name words for task matching. Python keeps snake_case splitting only (its class names are matched as
        entities), other languages also split camelCase / PascalCase."""
        return self.name.lower().split("_") if self.language == "python" else split_words(self.name)

    def label(self) -> str:
        return label_for(self.file, self.qualname)


def label_for(file: str, qualname: str) -> str:
    """`domain.update_order` (module + qualname); a Java/Kotlin/C# class already named like its file is not
    repeated: `OrderServiceImpl.approve`, not `OrderServiceImpl.OrderServiceImpl.approve`."""
    module = Path(file).stem
    return qualname if qualname == module or qualname.startswith(module + ".") else f"{module}.{qualname}"


class SymbolIndex:
    """Functions/classes/methods of one service with line ranges and referenced identifiers, any language.

    Complements the graphify code graph: graphify gives the symbol graph and
    communities; this index maps lines/fields/strings to their enclosing symbol.
    """

    def __init__(self, service: str) -> None:
        import conventions
        self.service = service
        self.symbols: list[Symbol] = []
        self.class_fields: dict[str, list[str]] = {}
        self.module_docs: dict[str, str] = {}         # file -> module docstring
        self.tables: dict[str, str] = {}              # class name -> table
        self.texts: dict[str, str] = {}               # file -> source text
        self.languages: set[str] = set()
        self.unparsed: list[str] = []                 # files no adapter could read (reported, never guessed)
        root = service_dir(service)
        for path in source_files(root, exclude=service_excludes(service)):
            self._index_file(path)
        cfg = {} if service == "common" else (registry().get(service) or {})
        self.conventions = conventions.select(cfg.get("conventions", "auto"), self.languages,
                                              list(self.texts.values()), ROOT)
        self._apply_conventions(conventions)

    def _index_file(self, path: Path) -> None:
        language = language_of(path)
        py, ts = _adapters()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        try:
            out = py.extract(text) if language == "python" else ts.extract(text, language)
        except ts.Unsupported:
            self.unparsed.append(rel(path))
            return
        file = rel(path)
        self.texts[file] = text
        self.languages.add(language)
        self.module_docs[file] = out.get("module_doc") or ""
        for s in out["symbols"]:
            self.symbols.append(Symbol(self.service, file, s["qualname"], s["kind"], s["start"], s["end"],
                                       set(s["refs"]), set(s["strings"]), list(s["decorators"]), s["signature"],
                                       s["docstring"], list(s["bases"]), dict(s["fields"]), language))
        for cls, fields in out.get("class_fields", {}).items():
            self.class_fields[cls] = list(fields)
        self.tables.update(out.get("tables") or {})

    def owner_of(self, sym: Symbol) -> Symbol | None:
        if "." not in sym.qualname:
            return None
        owner = sym.qualname.rsplit(".", 1)[0]
        return next((s for s in self.symbols if s.file == sym.file and s.qualname == owner and s.kind == "class"), None)

    def _apply_conventions(self, conventions) -> None:
        names = self.conventions
        route_rules = conventions.rules(names, ROOT, "routes")
        table_rules = conventions.rules(names, ROOT, "tables")
        consume_rules = conventions.rules(names, ROOT, "consumes")
        self.handlers: dict[str, str] = {}
        for sym in self.symbols:
            if sym.kind == "class":
                table = conventions.class_table(sym, table_rules) if table_rules else None
                if table:
                    self.tables.setdefault(sym.name, table)
                continue
            if route_rules:
                sym.route = conventions.decorator_route(sym, self.owner_of(sym), self.texts.get(sym.file, ""), route_rules)
            for topic in conventions.decorator_topics(sym, consume_rules) if consume_rules else []:
                self.handlers.setdefault(topic, sym.qualname)
        if any(r.get("on") == "source" for r in route_rules):
            for file, text in self.texts.items():
                for found in conventions.source_routes(text, route_rules):
                    target = self._handler_symbol(file, found)
                    if target is not None and target.route is None:
                        target.route = (found["method"], found["path"])

    def _handler_symbol(self, file: str, found: dict) -> Symbol | None:
        """The function a call-style route names (`router.get('/x', listItems)`), else the enclosing symbol."""
        handler = (found.get("handler") or "").split(".")[-1]
        if handler:
            cands = [s for s in self.product_symbols() if s.kind != "class" and s.name == handler
                     and (not found.get("class") or s.qualname.startswith(found["class"] + "."))]
            same_file = [s for s in cands if s.file == file]
            if same_file or cands:
                return (same_file or cands)[0]
        return None

    # lookups ---------------------------------------------------------------

    def product_symbols(self) -> list[Symbol]:
        return [s for s in self.symbols if not s.is_test]

    def enclosing(self, file: str, line: int) -> Symbol | None:
        best = None
        for sym in self.symbols:
            if sym.file == file and sym.start <= line <= sym.end:
                if best is None or sym.start >= best.start:
                    best = sym
        return best

    def for_graph_node(self, file: str, node: dict) -> Symbol | None:
        """The symbol a graphify node stands for: same file and name, disambiguated by the node's line
        (several classes in one file each have an `__init__`)."""
        name = node["label"].strip(".").rstrip("()")
        candidates = [s for s in self.symbols if s.file == file and s.name == name]
        line = str(node.get("source_location") or "").lstrip("L")
        if len(candidates) > 1 and line.isdigit():
            inside = [s for s in candidates if s.start <= int(line) <= s.end]
            candidates = sorted(inside, key=lambda s: -s.start) or candidates
        return candidates[0] if candidates else None

    def find(self, name: str) -> list[Symbol]:
        """Resolve 'update_order', 'domain.update_order', 'BillingClient.get_invoice' or 'OrderServiceImpl.approve'."""
        name = name.strip().rstrip("()")
        module = None
        if "." in name:
            head, tail = name.split(".", 1)
            if any(s.module == head for s in self.symbols):
                module, name = head, tail
        return [s for s in self.symbols
                if (s.qualname == name or s.name == name) and (module is None or s.module == module)]

    def referencing(self, identifiers: set[str], *, include_tests: bool = True) -> list[Symbol]:
        out = []
        for s in self.symbols:
            if not include_tests and s.is_test:
                continue
            hits = (s.refs | s.strings) & identifiers
            if s.kind == "class":
                hits -= set(self.class_fields.get(s.name, []))   # declaring a field is not reading it
            if hits:
                out.append(s)
        return out

    def dependents(self, seeds: list[Symbol], depth: int) -> dict[str, tuple[Symbol, int, str]]:
        """Reverse reference traversal: symbols that (transitively) reference the seeds."""
        found: dict[str, tuple[Symbol, int, str]] = {}
        frontier = seeds
        for level in range(1, depth + 1):
            names = {s.name for s in frontier}
            nxt = []
            for sym in self.symbols:
                if sym.key in found or any(sym.key == f.key for f in seeds):
                    continue
                hit = sym.refs & names
                if hit:
                    found[sym.key] = (sym, level, sorted(hit)[0])
                    nxt.append(sym)
            frontier = nxt
            if not frontier:
                break
        return found


@lru_cache
def symbol_index(service: str) -> SymbolIndex:
    return SymbolIndex(service)


def route_of(sym: Symbol) -> tuple[str, str] | None:
    """(METHOD, path) of an HTTP entry point, from the service's convention presets (FastAPI, Spring, JAX-RS,
    ASP.NET, NestJS, Express, gin, ... or config/conventions.yaml)."""
    return sym.route


def handler_topics(service: str) -> dict[str, str]:
    """topic -> handler qualname: a `HANDLERS` dict (python-servicekit) and handler annotations such as
    @KafkaListener / @RabbitListener / @EventPattern."""
    import conventions
    index = symbol_index(service)
    out = {}
    if "handlers_dict" in conventions.natives(index.conventions, ROOT):
        out.update(conventions.native_handlers_dict(package_dir(service) / "handlers.py"))
    for topic, qualname in index.handlers.items():
        out.setdefault(topic, qualname)
    return out


def publishers(service: str) -> list[dict]:
    """Event publications in the service's code -> [{topic, file, line, symbol}]."""
    import conventions
    index = symbol_index(service)
    found = []
    if "publish_event" in conventions.natives(index.conventions, ROOT):
        for path in sorted(package_dir(service).rglob("*.py")):
            if SKIP_PARTS & set(path.parts):
                continue
            for topic, line in conventions.native_publish_event(path):
                sym = index.enclosing(rel(path), line)
                found.append({"topic": topic, "file": rel(path), "line": line, "symbol": sym.label() if sym else None})
    publish_rules = conventions.rules(index.conventions, ROOT, "publishes")
    if publish_rules:
        for file, text in sorted(index.texts.items()):
            if is_test_path(file):
                continue
            for topic, line in conventions.source_topics(text, publish_rules):
                sym = index.enclosing(file, line)
                found.append({"topic": topic, "file": file, "line": line, "symbol": sym.label() if sym else None})
    return found


def _resolve_target(host: str | None) -> str | None:
    """A URL host / client name / property key -> registered service (name, or one of its `aliases`)."""
    if not host:
        return None
    services = registry()
    for name, cfg in services.items():
        names = {name, *(cfg.get("aliases") or [])}
        if host in names or host.split(".")[0] in names or any(host.startswith(n + "-") or host.startswith(n + ".")
                                                                for n in names):
            return name
    return None


def rest_calls(service: str) -> list[dict]:
    """Outbound HTTP calls to other services -> [{client, target, method, path, file, line}]."""
    import conventions
    index = symbol_index(service)
    calls = []
    if "service_client" in conventions.natives(index.conventions, ROOT):
        path = package_dir(service) / "clients.py"
        for call in conventions.native_service_client_calls(path):
            calls.append({**call, "file": rel(path)})
    client_rules = conventions.rules(index.conventions, ROOT, "clients")
    if not client_rules:
        return calls
    for sym in index.product_symbols():                      # declarative clients: Feign-style interfaces
        if sym.kind != "class":
            continue
        target = _resolve_target(conventions.client_target(sym, client_rules))
        if not target:
            continue
        for method in (s for s in index.product_symbols() if s.file == sym.file and s.qualname.startswith(sym.qualname + ".")):
            if method.route:
                calls.append({"client": method.qualname, "target": target, "method": method.route[0],
                              "path": method.route[1], "file": method.file, "line": method.start, "declarative": True})
    for file, text in sorted(index.texts.items()):             # imperative calls with the target in the URL
        if is_test_path(file):
            continue
        for found in conventions.source_calls(text, client_rules):
            target = _resolve_target(found["host"])
            if not target or target == service:
                continue
            sym = index.enclosing(file, found["line"])
            calls.append({"client": sym.qualname if sym else Path(file).stem, "target": target,
                          "method": found["method"], "path": found["path"], "file": file, "line": found["line"]})
    return calls


def migration_markers(service_names: list[str]) -> bool:
    """Schema-migration tooling in the repo: Alembic / Django migrations, Flyway, Liquibase, EF Core, TypeORM,
    Prisma, Rails, or brownfield.migrations.paths."""
    import conventions
    if any(ROOT.glob("**/alembic.ini")):
        return True
    globs = ["**/prisma/migrations", "**/db/migrate", "**/db/migration", "**/db/changelog", "**/Migrations",
             "**/migrations", "**/flyway.conf", "**/liquibase.properties"]
    configured = list((brownfield_config().get("migrations") or {}).get("paths") or [])
    if any((ROOT / p).exists() for p in configured):
        return True
    for service in service_names:
        if service in registry() or service == "common":
            globs += conventions.migration_globs(symbol_index(service).conventions, ROOT)
    for service in service_names:
        base = service_dir(service) if (service in registry() or service == "common") else None
        if base is None or not base.is_dir():
            continue
        for pattern in dict.fromkeys(globs):
            if any(p for p in base.glob(pattern) if not (SKIP_PARTS & set(p.relative_to(base).parts))):
                return True
    return False
