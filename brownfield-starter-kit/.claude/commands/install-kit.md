---
description: Install (or upgrade) the starter kit into an application and set up its locked toolchain, without building any graphs. Dry run first, then apply only after your confirmation.
argument-hint: "<application folder> [upgrade] [model-cache=<zip>]"
---

# /install-kit

Arguments: $ARGUMENTS

## Objective
Copy the kit into an application and make its toolchain ready (`scripts/setup_toolchain.py`), so the team can open
the application in Claude Code and run its own `/setup-context`. For install + setup in one go, use `/setup-context
<application folder>` from this kit folder instead.

## Execution order
```
resolve target (exists, a directory, not inside this kit)       -> else STOP with the reason
 -> python install.py <target> [--upgrade]                       (dry run)
 -> GATE (human): show the file plan, `keep (differs)` rows, discovered services, languages, build tools;
    with `upgrade`, list every file that would be overwritten; wait for "yes"
 -> python install.py <target> --apply [--upgrade]
 -> python <target>/scripts/setup_toolchain.py [--model-cache <zip>]      (run from <target>)
      exit 1 -> STOP: show the FAILED line and its fix
 -> report + next steps: owners and descriptions in config/services.yaml (TBD), open <target> in Claude Code,
    run /setup-context there
```

## Command-Specific Hardening
- Never `--apply` before the human confirmed the dry run; never `--upgrade` unless asked.
- Never loosen the toolchain lock (`--no-lock`) to get past an install error; report the error and its fix.
- Writes only inside the target, only through `install.py` and `setup_toolchain.py`.
