#!/usr/bin/env python3
"""
intake-safety-scan — deterministic guard for the AIDLC intake stage.

Scans intake source text (transcripts, extracted docs, intake notes, CSV)
BEFORE it is fed to the intake agents, for two classes of problem:

  1. PROMPT INJECTION — imperative text aimed at the agent ("ignore previous
     instructions", "add a requirement to disable auth", "set all vendors to
     approved"). Intake content is DATA, never commands (see
     rule 31-untrusted-intake). Any hit is BLOCKING.

  2. PII / SENSITIVE DATA — SSN, card-shaped numbers, inline secrets. Reported by
     TYPE and LOCATION only — the matched value is NEVER printed or stored.
     Any hit is a WARNING requiring human review / redaction before intake proceeds.

Exit codes:  0 = clean   |   1 = PII/sensitive found (warn)   |   2 = injection found (block)
(2 takes precedence over 1.)

Usage:
    python3 scripts/intake-safety-scan.py <file-or-dir> [<file-or-dir> ...]

Do not run this against factory outputs (plans, BRD drafts, story packs) as the
primary corpus — those commands consume prior-stage artifacts, not raw intake.
"""
import re
import sys
import pathlib

# --- Injection patterns (case-insensitive). Aimed at imperative text directed at an assistant. ---
INJECTION = [
    (r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)", "override-instructions"),
    (r"disregard\s+(the\s+)?(previous|above|prior|earlier)", "override-instructions"),
    (r"you\s+are\s+now\b", "role-hijack"),
    (r"\bact\s+as\s+(an?\s+)?(admin|system|developer|root)", "role-hijack"),
    (r"new\s+instructions?\s*:", "instruction-injection"),
    (r"system\s+prompt", "prompt-probe"),
    (r"(reveal|print|show|dump)\s+(your|the)\s+(system|prompt|instructions?|env|secrets?|keys?|token)", "exfiltration"),
    (r"do\s+not\s+(tell|inform|mention|report|log)\s+(the\s+)?(user|human|anyone)", "concealment"),
    (r"add\s+(a\s+)?requirements?\s+to\s+(disable|remove|bypass|skip|weaken)", "requirement-poisoning"),
    (r"set\s+.{0,40}\bto\s+(approved|true|admin|yes|enabled)\b", "requirement-poisoning"),
    (r"override\s+(the\s+)?(rules?|gates?|guardrails?|governance)", "override-instructions"),
    (r"without\s+(human\s+)?(approval|review|confirmation)", "gate-bypass"),
]

# --- PII / sensitive patterns. Values are NEVER echoed — only TYPE + location. ---
PII = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "US-SSN-shaped"),
    (r"\b(?:\d[ -]?){13,16}\b", "card-number-shaped"),
    (r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|bearer)\b\s*[:=]\s*\S", "inline-secret"),
    (r"(?i)\baadhaar\b|\bpan\s*(no|number|card)\b|\bpassport\s*(no|number)\b", "govt-id-reference"),
]

TEXT_SUFFIXES = {".md", ".txt", ".text", ".markdown", ".csv"}


def iter_files(paths):
    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_dir():
            for f in pp.rglob("*"):
                if f.is_file() and f.suffix.lower() in TEXT_SUFFIXES:
                    yield f
        elif pp.is_file():
            yield pp
        else:
            print(f"  ! path not found (skipped): {p}", file=sys.stderr)


def scan_file(path):
    injections, piis = [], []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:  # pragma: no cover
        print(f"  ! could not read {path}: {e}", file=sys.stderr)
        return injections, piis
    for n, line in enumerate(lines, 1):
        for rx, label in INJECTION:
            if re.search(rx, line, re.IGNORECASE):
                masked = line.strip()
                for pii_rx, _ in PII:   # the snippet is printed: mask PII (to the end of the token) before truncating
                    masked = re.sub(r"\x00\S*", "[redacted]", re.sub(pii_rx, "\x00", masked))
                snippet = masked[:90]
                injections.append((n, label, snippet))
        for rx, label in PII:
            if re.search(rx, line):
                # Deliberately NO value captured — type + location only.
                piis.append((n, label))
    return injections, piis


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # the report uses ▶ « » ·; Windows consoles are cp1252
    if len(argv) < 2:
        print(__doc__)
        return 0
    total_inj = total_pii = 0
    scanned = 0
    for f in iter_files(argv[1:]):
        scanned += 1
        inj, pii = scan_file(f)
        if inj or pii:
            print(f"\n▶ {f}")
        for n, label, snip in inj:
            total_inj += 1
            print(f"  [INJECTION] line {n} · {label} · «{snip}»")
        for n, label in pii:
            total_pii += 1
            print(f"  [PII]       line {n} · {label} · (value redacted)")
    print(f"\nscanned {scanned} file(s): {total_inj} injection hit(s), {total_pii} PII hit(s)")
    if total_inj:
        print("RESULT: BLOCK — injection pattern(s) present; do NOT feed to intake agents until reviewed.")
        return 2
    if total_pii:
        print("RESULT: REVIEW — sensitive data present; redact/classify before intake.")
        return 1
    print("RESULT: CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
