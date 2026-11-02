"""Install and verify the context-engine toolchain (Python packages + the embedding model) in one step.

    python scripts/setup_toolchain.py                       # create .venv-context, install, fetch the model, verify
    python scripts/setup_toolchain.py --check               # verify only: versions, imports, model offline, smoke
    python scripts/setup_toolchain.py --venv .venv          # Python repos: the repo's own environment
    python scripts/setup_toolchain.py --model-cache bge.zip # no Hugging Face access: import a teammate's export
    python scripts/setup_toolchain.py --export-model bge.zip  # share this machine's model with the team
    python scripts/setup_toolchain.py --torch-index default # torch from pip's configured index (internal mirror)

Why a script and not `pip install -r`: requirements.txt pins only the top-level packages, so every install resolved
a fresh set of transitive ones (transformers, huggingface_hub, tokenizers, numpy, ...) and teams ended up with
combinations nobody had tested. This script installs

  1. torch alone, from the CPU-only index (no multi-GB CUDA wheels), pinned by the lock;
  2. tools/context/requirements.txt with tools/context/constraints.txt, the exact versions verified together;
  3. the embedding model once, trusting the OS certificate store (TLS-inspecting proxies), retrying without the
     Xet transfer protocol, or from an exported cache (--model-cache) when huggingface.co is unreachable;

then proves the result offline (HF_HUB_OFFLINE=1): imports, `pip check`, drift against the lock, an embedding + FAISS
smoke and `graphify --help`. Proxy, mirror and cache settings come from the environment as usual (HTTPS_PROXY,
PIP_INDEX_URL, HF_ENDPOINT, HF_HOME). Standard library only: it runs before anything is installed.

Exit codes: 0 ready, 1 a step failed (the message says which and how to fix it), 2 bad arguments.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "tools" / "context" / "requirements.txt"
LOCK = ROOT / "tools" / "context" / "constraints.txt"
CONFIG = ROOT / ".claude" / "config.yaml"
KIT_BLOCK = "# --- brownfield context engine (starter kit)"   # what install.py appends to a Python repo's requirements
VERIFIED_PYTHON = (3, 12)
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
TORCH_CPU_INDEX = "https://download.pytorch.org/whl/cpu"
IMPORTS = ["yaml", "pytest", "graphify", "tree_sitter_java", "torch", "sentence_transformers", "faiss", "pypdf",
           "openpyxl", "truststore"]

# run inside the toolchain environment; argv: model name, "offline" | "download"
LOAD_MODEL = r"""
import sys
name, mode = sys.argv[1], sys.argv[2]
from sentence_transformers import SentenceTransformer
try:
    SentenceTransformer(name, device="cpu", local_files_only=True)
    print("cached")
except Exception as exc:
    if mode == "offline":
        raise SystemExit(f"not in the local cache: {exc}")
    try:  # TLS-inspecting proxy: trust the OS certificate store, as pip >= 24.2 does
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass
    SentenceTransformer(name, device="cpu")
    print("downloaded")
"""

SMOKE = r"""
import sys
import faiss
from sentence_transformers import SentenceTransformer
vectors = SentenceTransformer(sys.argv[1], device="cpu", local_files_only=True).encode(
    ["cancel an order", "reject a price below cost"], normalize_embeddings=True)
index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)
print(f"embedding dim {vectors.shape[1]}, faiss ntotal {index.ntotal}")
"""


class Failed(Exception):
    """A step failed; the message says what to do."""


def say(step: str, text: str) -> None:
    print(f"[{step}] {text}", flush=True)


def env_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list, env: dict | None = None, capture: bool = False) -> subprocess.CompletedProcess:
    full = {**os.environ, **(env or {})}
    full.setdefault("PYTHONUTF8", "1")
    full.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    return subprocess.run([str(c) for c in cmd], env=full, text=True, capture_output=capture)


def model_name(override: str | None) -> str:
    """brownfield.semantic.model from .claude/config.yaml (read without PyYAML, which may not be installed yet)."""
    if override:
        return override
    if CONFIG.exists():
        match = re.search(r"^\s+semantic:[^\n]*\n(?:[ \t]+[^\n]*\n|\s*\n)*?[ \t]+model:\s*['\"]?([^\s'\"#]+)",
                          CONFIG.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1)
    return DEFAULT_MODEL


def lock_pins() -> dict[str, str]:
    pins = {}
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if "==" in line:
            name, version = line.split("==", 1)
            pins[normalise(name)] = version.strip()
    return pins


def normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# --------------------------------------------------------------------------- steps


def check_interpreter(python: Path, label: str) -> None:
    out = run([python, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"], capture=True)
    if out.returncode:
        raise Failed(f"{label} does not run: {out.stderr.strip()}")
    version = tuple(int(p) for p in out.stdout.strip().split("."))
    if version < (3, 10):
        raise Failed(f"{label} is Python {out.stdout.strip()}; the tools need 3.10+. Install Python "
                     f"{VERIFIED_PYTHON[0]}.{VERIFIED_PYTHON[1]} and rerun with it "
                     f"(Windows: py -{VERIFIED_PYTHON[0]}.{VERIFIED_PYTHON[1]} scripts/setup_toolchain.py)")
    say("python", f"{label}: Python {out.stdout.strip()}")
    if version[:2] != VERIFIED_PYTHON:
        say("python", f"WARNING: the lock was verified on Python {VERIFIED_PYTHON[0]}.{VERIFIED_PYTHON[1]}. Newer "
                      "Pythons often have no torch / faiss-cpu wheels yet (pip then reports 'No matching "
                      "distribution'). If a step fails, recreate the environment with "
                      f"{VERIFIED_PYTHON[0]}.{VERIFIED_PYTHON[1]}.")


def ensure_venv(venv: Path, create: bool) -> Path:
    python = env_python(venv)
    if python.exists():
        say("venv", f"using {venv}")
    elif not create:
        raise Failed(f"no environment at {venv}: run `python scripts/setup_toolchain.py` first (or pass --venv)")
    else:
        say("venv", f"creating {venv}")
        if run([sys.executable, "-m", "venv", venv]).returncode:
            raise Failed(f"`python -m venv {venv}` failed; on Debian/Ubuntu install the python3-venv package")
    check_interpreter(python, f"environment {venv.name}")
    return python


def ensure_pip(python: Path) -> None:
    out = run([python, "-m", "pip", "--version"], capture=True)
    match = re.match(r"pip (\d+)\.(\d+)", out.stdout)
    if match and (int(match.group(1)), int(match.group(2))) >= (24, 2):
        say("pip", out.stdout.split(" from ")[0] + " (uses the OS certificate store)")
        return
    say("pip", f"{out.stdout.split(' from ')[0] or 'pip'} is older than 24.2: upgrading")
    if run([python, "-m", "pip", "install", "--upgrade", "pip>=24.2"]).returncode:
        say("pip", "WARNING: upgrade failed; continuing. Behind a TLS-inspecting proxy, older pip needs the company "
                   "root CA (PIP_CERT=<bundle.pem>); never use --trusted-host")


def install_torch(python: Path, torch_index: str, use_lock: bool) -> None:
    pin = lock_pins().get("torch")
    # --no-deps: torch's own dependencies come in the next step, from the normal index and pinned by the lock
    cmd = [python, "-m", "pip", "install", "--no-deps", "torch" + (f"=={pin}" if pin and use_lock else "")]
    if torch_index != "default":
        cmd += ["--index-url", torch_index]
    say("torch", "installing " + cmd[5] + (f" from {torch_index}" if torch_index != "default" else
                                            " from pip's configured index"))
    if run(cmd).returncode:
        raise Failed("torch did not install. Typical causes: no wheel for this Python (use "
                     f"{VERIFIED_PYTHON[0]}.{VERIFIED_PYTHON[1]}); download.pytorch.org blocked (use the internal "
                     "mirror: --torch-index default, or --torch-index <mirror>/whl/cpu); proxy (set HTTPS_PROXY)")


def install_requirements(python: Path, use_lock: bool) -> None:
    # torch is already in place, so the CPU index line is dropped here: pip would otherwise query
    # download.pytorch.org for every package (slow, and a frequent timeout behind corporate proxies)
    kit_requirements = Path(tempfile.mkdtemp()) / "requirements.txt"
    kit_requirements.write_text("\n".join(l for l in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
                                          if not l.lstrip().startswith(("--extra-index-url", "--index-url"))),
                                encoding="utf-8")
    cmd = [python, "-m", "pip", "install", "-r", kit_requirements]
    repo_requirements = ROOT / "requirements.txt"
    shared = repo_requirements.exists() and KIT_BLOCK in repo_requirements.read_text(encoding="utf-8")
    if shared:
        cmd += ["-r", repo_requirements]                # Python repo: app and tools share one environment
    if use_lock:
        cmd += ["-c", LOCK]
    shown = [REQUIREMENTS if c == kit_requirements else c for c in cmd[4:]]
    say("packages", "installing " + " ".join(str(c.relative_to(ROOT)) if isinstance(c, Path) else c for c in shown))
    result = run(cmd)
    shutil.rmtree(kit_requirements.parent, ignore_errors=True)
    if result.returncode:
        hint = ("This Python repo installs its own requirements.txt into the same environment (its tests run in it): "
                "if pip reports a conflict, a repo pin disagrees with tools/context/constraints.txt; align that pin "
                "as a normal change, or ask the kit owner to re-verify the lock. "
                if shared else "")
        raise Failed("package install failed (see pip's message above). " + hint +
                     "Never loosen the lock to get past a conflict; report it to the kit owner. A proxy needs "
                     "HTTPS_PROXY; an internal mirror needs PIP_INDEX_URL.")


def verify_packages(python: Path, use_lock: bool) -> None:
    out = run([python, "-c", "import " + ", ".join(IMPORTS)], capture=True)
    if out.returncode:
        missing = re.search(r"No module named '([^']+)'", out.stderr)
        raise Failed(f"import check failed ({missing.group(1) if missing else out.stderr.strip()[-300:]}): this "
                     "environment is not the one the packages went into, or the install was interrupted; rerun "
                     "the script without --check")
    say("imports", "ok: " + ", ".join(IMPORTS))
    out = run([python, "-m", "pip", "check"], capture=True)
    if out.returncode:
        raise Failed("pip check found incompatible packages:\n" + out.stdout.strip() +
                     "\nRerun the script without --check (it reinstalls from the lock)")
    say("pip check", "no broken requirements")
    if not use_lock:
        return
    out = run([python, "-m", "pip", "list", "--format=freeze"], capture=True)
    installed = {normalise(n): v.split("+")[0] for n, v in
                 (l.split("==", 1) for l in out.stdout.splitlines() if "==" in l)}
    drift = [f"{name} {installed[name]} (lock {want})" for name, want in lock_pins().items()
             if name in installed and installed[name] != want]
    if drift:
        say("lock", "WARNING: differs from tools/context/constraints.txt: " + ", ".join(drift) +
                    ". Rerun without --check to align")
    else:
        say("lock", "every installed toolchain package matches the lock")


def hub_cache(python: Path) -> Path:
    out = run([python, "-c", "from huggingface_hub.constants import HF_HUB_CACHE; print(HF_HUB_CACHE)"],
              capture=True)
    if out.returncode:
        raise Failed("huggingface_hub is not importable; install the packages first")
    return Path(out.stdout.strip())


def repo_folder(name: str) -> str:
    return "models--" + name.replace("/", "--")


def import_model(python: Path, name: str, source: Path) -> None:
    """Copy an exported Hugging Face cache entry (zip from --export-model, or a models--org--name folder)."""
    cache, folder = hub_cache(python), repo_folder(name)
    if source.is_dir():
        src = source if source.name == folder else source / folder
        if not (src / "snapshots").is_dir():
            raise Failed(f"{source} is not a Hugging Face cache entry for {name} (expected {folder}/snapshots/)")
        shutil.copytree(src, cache / folder, dirs_exist_ok=True)
    elif zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            members = archive.namelist()
            bad = [m for m in members if not m.startswith(folder + "/") or ".." in Path(m).parts]
            if bad or not any(m.startswith(f"{folder}/snapshots/") for m in members):
                raise Failed(f"{source} is not an export of {name}: entries must sit under {folder}/ "
                             "(create it with --export-model)")
            archive.extractall(cache)
    else:
        raise Failed(f"--model-cache {source}: neither a folder nor a zip file")
    say("model", f"imported {name} into {cache}")


def export_model(python: Path, name: str, target: Path) -> None:
    """Zip refs/ and snapshots/ (symlinks resolved), enough for local_files_only loading on any OS."""
    src = hub_cache(python) / repo_folder(name)
    if not (src / "snapshots").is_dir():
        raise Failed(f"{name} is not in this machine's cache ({src}); fetch it first")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(src.rglob("*")):
            rel = path.relative_to(src)
            if rel.parts[0] in ("refs", "snapshots") and path.is_file():
                archive.write(path.resolve(), f"{repo_folder(name)}/{rel.as_posix()}")
    say("model", f"exported {name} to {target} ({target.stat().st_size // (1024 * 1024)} MB). Share it; teammates "
                 "run: python scripts/setup_toolchain.py --model-cache <zip>")


def ensure_model(python: Path, name: str, offline: bool) -> None:
    out = run([python, "-c", LOAD_MODEL, name, "offline"], env={"HF_HUB_OFFLINE": "1"}, capture=True)
    if out.returncode == 0:
        say("model", f"{name}: in the local cache")
        return
    if offline:
        raise Failed(f"{name} is not in the local cache: rerun without --check, or import a teammate's export "
                     "with --model-cache <zip>")
    say("model", f"downloading {name} (once, about 130 MB)")
    for attempt, env in (("", {}), (" without Xet", {"HF_HUB_DISABLE_XET": "1"})):
        out = run([python, "-c", LOAD_MODEL, name, "download"], env=env, capture=True)
        if out.returncode == 0:
            say("model", f"{name}: downloaded{attempt}")
            return
        say("model", f"download{attempt} failed: " + (out.stderr.strip().splitlines() or ["?"])[-1][:300])
    raise Failed("the embedding model could not be downloaded. Options, in order: set HTTPS_PROXY to the company "
                 "proxy; set HF_ENDPOINT to an internal Hugging Face mirror; or ask a teammate who has it for "
                 "`python scripts/setup_toolchain.py --export-model bge.zip` and run this script with "
                 "--model-cache bge.zip. Never switch semantic search off instead (manifests require it)")


def smoke(python: Path, name: str) -> None:
    out = run([python, "-c", SMOKE, name], env={"HF_HUB_OFFLINE": "1"}, capture=True)
    if out.returncode:
        raise Failed("offline embedding smoke failed:\n" + out.stderr.strip()[-600:])
    say("smoke", "offline " + out.stdout.strip())
    graphify = shutil.which("graphify", path=str(python.parent))
    if not graphify or run([graphify, "--help"], capture=True).returncode:
        raise Failed(f"`graphify --help` failed in {python.parent}; rerun without --check")
    say("smoke", "graphify --help ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--venv", type=Path, default=ROOT / ".venv-context",
                        help="environment to create / use (default: .venv-context at the repo root)")
    parser.add_argument("--check", action="store_true", help="verify only; install nothing")
    parser.add_argument("--model", help=f"embedding model (default: brownfield.semantic.model, else {DEFAULT_MODEL})")
    parser.add_argument("--model-cache", type=Path, help="import the model from an --export-model zip or folder")
    parser.add_argument("--export-model", type=Path, help="zip this machine's cached model for teammates, then stop")
    parser.add_argument("--torch-index", default=TORCH_CPU_INDEX,
                        help="index for torch: a URL, or 'default' for pip's configured index / mirror")
    parser.add_argument("--no-lock", action="store_true",
                        help="skip tools/context/constraints.txt (diagnosis only: the result is untested)")
    args = parser.parse_args()
    if not REQUIREMENTS.exists() or (not args.no_lock and not LOCK.exists()):
        print(f"missing {REQUIREMENTS.relative_to(ROOT)} or {LOCK.relative_to(ROOT)}: rerun the starter kit's "
              "install.py <repo> --apply", file=sys.stderr)
        return 2
    venv = args.venv if args.venv.is_absolute() else (Path.cwd() / args.venv)
    name = model_name(args.model)
    try:
        if not args.check:
            check_interpreter(Path(sys.executable), "this python")
        python = ensure_venv(venv, create=not (args.check or args.export_model))
        if args.export_model:
            export_model(python, name, args.export_model.resolve())
            return 0
        if not args.check:
            ensure_pip(python)
            install_torch(python, args.torch_index, use_lock=not args.no_lock)
            install_requirements(python, use_lock=not args.no_lock)
        verify_packages(python, use_lock=not args.no_lock)
        if args.model_cache and not args.check:
            import_model(python, name, args.model_cache.resolve())
        ensure_model(python, name, offline=args.check)
        smoke(python, name)
    except Failed as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        return 1
    activate = venv / "Scripts" / "activate" if os.name == "nt" else f". {venv / 'bin' / 'activate'}"
    print(f"\nToolchain ready. Activate it in every shell that runs the tools: {activate}\n"
          "Agents and commands must use this same python. Next: /setup-context (docs/01-SETUP.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
