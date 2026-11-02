"""Install the brownfield starter kit into an existing repository.

    python install.py <application-folder>          # dry run: the discovered layout + what would be copied
    python install.py <target-repo> --apply         # do it
    python install.py <target-repo> --apply --upgrade   # also overwrite kit-owned files (tools, scripts, kit .claude
                                                        # files) that differ from this kit version

Never overwrites a file the target already has, except kit-owned files with --upgrade. Files that need a human merge
(an existing .claude/config.yaml, a different CLAUDE.md) are reported, not touched. Standard library only: runs before
any `pip install`. Writes nothing outside <target-repo>. Does not run git.

Any language: the tools run on Python, the code they read can be Java, Kotlin, C#, TypeScript, JavaScript, Go, Ruby,
PHP, Rust, Scala, Swift, Groovy, C/C++ or Python. The installer reports the languages it finds; Python-only scaffold
(pytest.ini, .coveragerc) is installed only into Python repos, and
the toolchain requirements go to tools/context/requirements.txt (appended to requirements.txt only in Python repos).

The target is just the application folder: a repository or not (git is optional), one service or a folder of
many (services, shared library, QA test cases side by side). The layout is discovered from build files and folders
(tools/context/discover.py) and written as config/services.yaml + the brownfield layout; a human only confirms the
owners and descriptions. After installing, open the folder in Claude Code and run /setup-context (docs/01-SETUP.md).
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

KIT_VERSION = "2.2.0"
HERE = Path(__file__).resolve().parent
KIT = HERE / "kit"
SKIP = {"__pycache__", ".pytest_cache"}

# kit-owned: identical in every repo; --upgrade may overwrite them
OWNED = [
    (KIT / ".claude", ".claude"),
    (KIT / "tools" / "context", "tools/context"),
    (KIT / "scripts", "scripts"),
    (KIT / "reference-tests", "tools/context/reference-tests"),
    (HERE / "docs", "docs/context-engine/starter-kit"),
]
NEVER_OVERWRITE = {".claude/config.yaml"}          # repo-specific once filled in: merged by a human / /setup-context
SCAFFOLD = KIT / "scaffold"
sys.path.insert(0, str(KIT / "tools" / "context"))
import discover  # noqa: E402  (standard library only, like this installer)
SCAFFOLD_SPECIAL = {"gitignore-snippet.txt", "requirements-context.txt", "constraints-context.txt",
                    "CLAUDE-brownfield-snippet.md"}
PYTHON_ONLY = {"pytest.ini", ".coveragerc"}
CLAUDE_MARKER = "## Brownfield change path (starter kit)"
LANGUAGES = {".py": "python", ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".cs": "csharp", ".ts": "typescript",
             ".tsx": "typescript", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".go": "go",
             ".rb": "ruby", ".php": "php", ".rs": "rust", ".scala": "scala", ".swift": "swift", ".groovy": "groovy",
             ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp"}
NOT_SOURCE = {".git", ".venv", "venv", "node_modules", "target", "build", "dist", "out", "bin", "obj", ".gradle",
              "vendor", "__pycache__", "graphify-out", ".idea", ".vs", "coverage", ".next"}
BUILD_MARKERS = {"pom.xml": "Maven", "build.gradle": "Gradle", "build.gradle.kts": "Gradle", "package.json": "npm",
                 "go.mod": "Go modules", "Cargo.toml": "Cargo", "composer.json": "Composer", "Gemfile": "Bundler",
                 "pyproject.toml": "Python project", "requirements.txt": "pip", "setup.py": "setuptools"}


def detect(target: Path) -> tuple[dict[str, int], list[str]]:
    """Source files per language (the kit's own files excluded) and build tools found at the top two levels."""
    counts: dict[str, int] = {}
    kit = {"tools/context", ".claude", "scripts/_paths.py", "scripts/graphify_all.py", "scripts/run_tests.py",
           "scripts/intake-safety-scan.py"}
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in LANGUAGES:
            continue
        r = path.relative_to(target)
        if NOT_SOURCE & set(r.parts) or any(r.as_posix() == k or r.as_posix().startswith(k + "/") for k in kit):
            continue
        lang = LANGUAGES[path.suffix.lower()]
        counts[lang] = counts.get(lang, 0) + 1
    builds = sorted({f"{tool} ({p.relative_to(target).as_posix()})" for marker, tool in BUILD_MARKERS.items()
                     for p in list(target.glob(marker)) + list(target.glob(f"*/{marker}"))})
    return dict(sorted(counts.items(), key=lambda kv: -kv[1])), builds


def files_under(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not SKIP & set(path.parts):
            yield path


class Plan:
    def __init__(self, target: Path, apply: bool, upgrade: bool):
        self.target, self.apply, self.upgrade = target, apply, upgrade
        self.rows: list[tuple[str, str]] = []           # (action, path)

    def note(self, action: str, path: str) -> None:
        self.rows.append((action, path))

    def copy(self, src: Path, rel: str, owned: bool) -> None:
        dst = self.target / rel
        if not dst.exists():
            self.note("copy", rel)
        elif filecmp.cmp(src, dst, shallow=False):
            return
        elif owned and self.upgrade and rel not in NEVER_OVERWRITE:
            self.note("upgrade", rel)
        else:
            self.note("keep (differs)" if owned else "keep (exists)", rel)
            return
        if self.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def append_lines(self, rel: str, lines: list[str], header: str) -> None:
        """Append the lines the file does not already contain (exact match, ignoring surrounding spaces)."""
        dst = self.target / rel
        existing = dst.read_text(encoding="utf-8").splitlines() if dst.exists() else []
        have = {l.strip() for l in existing}
        missing = [l for l in lines if l.strip() and not l.lstrip().startswith("#") and l.strip() not in have]
        if not missing:
            return
        self.note(f"append {len(missing)} line(s)" if dst.exists() else "create", rel)
        if self.apply:
            text = "\n".join(existing).rstrip("\n")
            text = (text + "\n\n" if text else "") + header + "\n" + "\n".join(missing) + "\n"
            dst.write_text(text, encoding="utf-8")


def package_name(line: str) -> str | None:
    line = line.split("#")[0].strip()
    if not line or line.startswith("-"):
        return None
    return re.split(r"[=<>!~\[; ]", line, maxsplit=1)[0].lower().replace("_", "-")


def install_requirements(plan: Plan, python_repo: bool) -> None:
    """The toolchain pins always go to tools/context/requirements.txt (kit-owned). A Python repo also gets them in
    its requirements.txt (one environment for app and tools); other repos keep the tools' environment separate.
    The lock (every transitive version verified together) is applied by scripts/setup_toolchain.py."""
    plan.copy(SCAFFOLD / "requirements-context.txt", "tools/context/requirements.txt", owned=True)
    plan.copy(SCAFFOLD / "constraints-context.txt", "tools/context/constraints.txt", owned=True)
    if not python_repo:
        return
    src = (SCAFFOLD / "requirements-context.txt").read_text(encoding="utf-8").splitlines()
    dst = plan.target / "requirements.txt"
    existing = dst.read_text(encoding="utf-8").splitlines() if dst.exists() else []
    have = {package_name(l) for l in existing} | {l.strip() for l in existing}
    wanted = [l for l in src if (package_name(l) and package_name(l) not in have)
              or (l.startswith("--extra-index-url") and l.strip() not in have)]
    if wanted:
        plan.append_lines("requirements.txt", wanted, "# --- brownfield context engine (starter kit)")
    pinned_elsewhere = [package_name(l) for l in src if package_name(l) and package_name(l) in have
                        and l.strip() not in {e.strip() for e in existing}]
    if pinned_elsewhere:
        plan.note("check pins (kept yours)", "requirements.txt: " + ", ".join(sorted(set(pinned_elsewhere))))


def install_claude_md(plan: Plan) -> None:
    snippet = (SCAFFOLD / "CLAUDE-brownfield-snippet.md").read_text(encoding="utf-8")
    dst = plan.target / "CLAUDE.md"
    if dst.exists() and CLAUDE_MARKER in dst.read_text(encoding="utf-8"):
        text = dst.read_text(encoding="utf-8")
        start = text.index(CLAUDE_MARKER)
        following = re.search(r"^## ", text[start + len(CLAUDE_MARKER):], re.MULTILINE)
        end = start + len(CLAUDE_MARKER) + following.start() if following else len(text)
        if text[start:end].strip() == snippet.strip():
            return
        if not plan.upgrade:
            plan.note("keep (differs)", "CLAUDE.md (brownfield section)")
            return
        plan.note("upgrade", "CLAUDE.md (brownfield section)")
        if plan.apply:
            rest = text[end:].lstrip("\n")
            dst.write_text(text[:start] + snippet.rstrip("\n") + "\n" + ("\n" + rest if rest else ""),
                           encoding="utf-8")
        return
    plan.note("append section" if dst.exists() else "create", "CLAUDE.md")
    if plan.apply:
        text = dst.read_text(encoding="utf-8").rstrip("\n") + "\n\n" if dst.exists() else "# CLAUDE.md\n\n"
        dst.write_text(text + snippet, encoding="utf-8")


def stamp(plan: Plan) -> None:
    digest = hashlib.sha1()
    for src_root, _ in OWNED:
        for path in files_under(src_root):
            digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    rel = ".claude/brownfield-kit.json"
    plan.note("write", rel)
    if plan.apply:
        (plan.target / rel).write_text(json.dumps(
            {"kit": "brownfield-starter-kit", "version": KIT_VERSION, "installed": date.today().isoformat(),
             "kit_digest": digest.hexdigest()[:16]}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--apply", action="store_true", help="write files (default: dry run)")
    parser.add_argument("--upgrade", action="store_true", help="overwrite kit-owned files that differ")
    parser.add_argument("--no-discover", action="store_true", help="do not write the discovered layout")
    args = parser.parse_args()
    target = args.target.resolve()
    if not target.is_dir():
        raise SystemExit(f"not a directory: {target}")
    if target == HERE or HERE in target.parents:
        raise SystemExit("target is inside the starter kit; point it at the repository to onboard")
    if not (target / ".git").exists():
        print(f"note: {target} has no git repository. That is fine: freshness is content-based. Without git, "
              "manifests carry no change history and the files a change touched are found from content snapshots.")

    languages, builds = detect(target)
    layout = discover.plan(target)            # services, shared library, tests, QA, rules: from the folder alone
    found = layout["services"] + ([{"language": "python"}] if layout["common"] and layout["common"].get("package")
                                  and (target / layout["common"]["path"] / layout["common"]["package"] / "__init__.py").exists() else [])
    python_repo = any(s.get("language") == "python" for s in found) or (not found and "python" in languages)
    plan = Plan(target, args.apply, args.upgrade)
    for src_root, dst_root in OWNED:
        for path in files_under(src_root):
            plan.copy(path, f"{dst_root}/{path.relative_to(src_root).as_posix()}", owned=True)
    for path in files_under(SCAFFOLD):
        rel_path = path.relative_to(SCAFFOLD).as_posix()
        if path.name in SCAFFOLD_SPECIAL or (rel_path in PYTHON_ONLY and not python_repo):
            continue
        plan.copy(path, rel_path, owned=False)
    plan.append_lines(".gitignore", (SCAFFOLD / "gitignore-snippet.txt").read_text(encoding="utf-8").splitlines(),
                      "# --- brownfield context engine (starter kit)")
    install_requirements(plan, python_repo)
    install_claude_md(plan)
    stamp(plan)

    width = max((len(a) for a, _ in plan.rows), default=0)
    for action, rel in plan.rows:
        print(f"  {action:<{width}}  {rel}")
    counts: dict[str, int] = {}
    for action, _ in plan.rows:
        counts[action.split(" ")[0]] = counts.get(action.split(" ")[0], 0) + 1
    print("\n" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    differs = [r for a, r in plan.rows if a == "keep (differs)"]
    if differs:
        print(f"\n{len(differs)} kit file(s) already exist with other content and were kept. Review them, or rerun "
              "with --upgrade to take this kit's version.")
    if (target / ".claude" / "config.yaml").exists() and "brownfield:" not in (
            target / ".claude" / "config.yaml").read_text(encoding="utf-8"):
        print("\n.claude/config.yaml exists without a `brownfield:` block: copy the block from "
              f"{(KIT / '.claude' / 'config.yaml').as_posix()} (or let /setup-context do it).")
    print("\nlanguages: " + (", ".join(f"{k} ({v} files)" for k, v in languages.items()) or "none found")
          + ("\nbuild tools: " + ", ".join(builds) if builds else ""))
    if not python_repo:
        print("toolchain: python scripts/setup_toolchain.py (creates .venv-context, installs the locked versions, "
              "fetches the model; the tools need Python 3.10+, the code can stay in any language)")
    print("\n" + discover.report(layout))
    if not args.apply:
        print("\nDry run. Rerun with --apply to install (the layout above is written to config/services.yaml and "
              ".claude/config.yaml).")
    else:
        if not args.no_discover:
            written = discover.write(target, layout)
            print("\nlayout written: " + (", ".join(written) or "nothing (config/services.yaml already lists services; "
                                          "`python tools/context/discover.py --write --force` replaces it)"))
        print("\nInstalled. Next: `python scripts/setup_toolchain.py` in the repo, confirm owners + descriptions in "
              "config/services.yaml (TBD), then open this folder in Claude Code and run /setup-context "
              "(docs/01-SETUP.md). Or, from the starter kit folder in Claude Code: /setup-context <this folder>.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
