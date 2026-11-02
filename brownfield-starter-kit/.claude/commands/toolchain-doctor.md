---
description: Diagnose (and, with your OK, repair) an application's context-engine toolchain — Python version, locked package versions, imports, pip check, the embedding model in the local cache, offline embedding + FAISS smoke, graphify. Use when installs fail with Hugging Face, torch, numpy or other package errors.
argument-hint: "<application folder> [repair] [model-cache=<zip>] [export-model=<zip>]"
---

# /toolchain-doctor

Arguments: $ARGUMENTS

## Objective
Tell the team exactly what is wrong with a toolchain and the one fix for it, using the target's
`scripts/setup_toolchain.py` (installed by the kit), so nobody pins, upgrades or uninstalls packages by hand.

## Execution order
```
resolve target; <target>/scripts/setup_toolchain.py missing -> the kit is not installed (or older than 2.2.0):
    suggest /install-kit <target> [upgrade]; STOP
 -> python scripts/setup_toolchain.py --check                 (run from <target>; installs nothing)
 -> exit 0: report "ready" + the python to use
 -> exit 1: explain the FAILED line in plain words, with the fix it names. Common ones:
      - Python other than 3.12 + "No matching distribution"    -> recreate the venv with 3.12
      - drift against the lock / pip check broken             -> repair (below)
      - model not in the cache, download blocked              -> HTTPS_PROXY, HF_ENDPOINT mirror, or a teammate's
                                                                 export (export-model= on their machine, model-cache= here)
 -> [repair, after the human says yes] python scripts/setup_toolchain.py [--model-cache <zip>], then --check again
 -> [export-model=<zip>] python scripts/setup_toolchain.py --export-model <zip>  (to share the model)
```

## Command-Specific Hardening
- `--check` first, always; repair only with the human's yes.
- Never `--no-lock`, never `pip install --upgrade <pkg>` by hand, never switch semantic search off, never
  `--trusted-host` or disabled certificate checks. Proxy and CA problems are fixed with the company proxy, mirror or
  certificate store.
- Never print tokens, proxy passwords or credentials found in the environment.
