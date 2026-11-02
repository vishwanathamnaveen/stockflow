"""Document knowledge base: retrieval over PDFs, spreadsheets and notes, for agents to query with citations.

    python tools/context/knowledge_base.py build                    # incremental; --full re-extracts and re-embeds
    python tools/context/knowledge_base.py search "supplier lead time for perishables" -k 5
    python tools/context/knowledge_base.py search "returns policy" --expand "refund window days" --json
    python tools/context/knowledge_base.py status                   # freshness, excluded passages, warnings

Sources: every .pdf / .xlsx / .xlsm / .csv / .md / .txt under `brownfield.knowledge_base.roots` (default `knowledge/`).
  pdf         one passage per page (split when long)          locator `p.3`, `p.3 (2/3)`
  xlsx, csv   rows rendered "Header: value; ..." in row groups  locator `Sheet1!rows 2-14`
  md, txt     sections split at headings, then by length       locator `§2`, `§2 (1/2)`

This is retrieval only (the R of RAG): it returns passages and where they came from. The agent that reads them is
the generator, so no LLM runs here and nothing leaves the machine. Same engine as semantic_index.py: local
sentence-transformers model, FAISS exact cosine + BM25, reciprocal-rank fusion, vectors reused by text hash.

Safety: passages are data, never instructions (rule 31). Each passage is screened with the patterns of
scripts/intake-safety-scan.py: injection-shaped text is quarantined, sensitive-data-shaped text (ID numbers, card
numbers, inline secrets) is excluded. Both are reported by source, locator and type only; the text is never stored.

Knowledge is context, not scope: a passage never adds files to a Context Manifest and never changes its scores.
Freshness is content-based: stale when a source file's bytes, the chunking settings, the screen or the model change.
Index files (graphs/kb/, git-ignored) are replaced atomically, meta.json last with checksums of the others.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import re
import sys
import time
from collections import Counter
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (GRAPHS, KB_SUFFIXES, ROOT, brownfield_config, data_digest, file_digest, head_commit,  # noqa: E402
                    kb_roots, load_json, rel, write_atomic)

KB_DIR = GRAPHS / "kb"
KB_VERSION = 1          # bump when extraction or chunking output changes: older indexes read as stale
DEFAULTS = {"chunk_chars": 1200, "overlap": 150, "top_k": 5, "min_dense_score": 0.60}
SCANNER = ROOT / "scripts" / "intake-safety-scan.py"


def settings() -> dict:
    import semantic_index
    sem = semantic_index.settings()
    cfg = {**DEFAULTS, **{k: v for k, v in (brownfield_config().get("knowledge_base") or {}).items() if k != "roots"}}
    return {**cfg, "model": sem["model"], "query_prefix": sem["query_prefix"]}


def settings_digest(cfg: dict | None = None) -> str:
    cfg = cfg or settings()
    return data_digest({"version": KB_VERSION, "chunk_chars": cfg["chunk_chars"], "overlap": cfg["overlap"],
                        "screen": _screen_digest()})


# --------------------------------------------------------------------------- safety screen


@lru_cache
def _scanner():
    spec = importlib.util.spec_from_file_location("intake_safety_scan", SCANNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _screen_digest() -> str:
    s = _scanner()
    return data_digest([s.INJECTION, s.PII])


def screen(text: str) -> tuple[str, list[str]] | None:
    """('injection'|'sensitive', labels) when a passage must not be indexed; None when it is clean."""
    s = _scanner()
    inj = sorted({label for rx, label in s.INJECTION if re.search(rx, text, re.IGNORECASE)})
    if inj:
        return "injection", inj
    pii = sorted({label for rx, label in s.PII if re.search(rx, text)})
    return ("sensitive", pii) if pii else None


# --------------------------------------------------------------------------- extraction


def sources() -> list[Path]:
    out = []
    for root in kb_roots():
        if root.is_dir():
            out += [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix.lower() in KB_SUFFIXES
                    and not p.name.startswith(("~$", "."))]          # Office lock files, hidden files
    return out


def split(text: str, size: int, overlap: int) -> list[str]:
    """Windows of at most `size` characters, broken at whitespace, overlapping by about `overlap`."""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) <= size:
        return [text] if text else []
    parts, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            cut = text.rfind(" ", start + size // 2, end)
            end = cut if cut > start else end
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        while start < end and not text[start - 1].isspace():   # begin the overlap on a word boundary
            start += 1
    return [p for p in parts if p]


def _numbered(locator: str, parts: list[str]) -> list[tuple[str, str]]:
    return [(locator if len(parts) == 1 else f"{locator} ({i}/{len(parts)})", p) for i, p in enumerate(parts, 1)]


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value).strip()


def _table(name: str, rows: list[tuple[int, list]], size: int) -> tuple[list[tuple[str, str]], list[str]]:
    """Header row + data rows -> row groups; each row keeps its header names so a lone row still means something."""
    rows = [(n, [_cell(v) for v in r]) for n, r in rows]
    rows = [(n, r) for n, r in rows if any(r)]
    if not rows:
        return [], []
    _, header = rows[0]
    header = [h or f"column {j + 1}" for j, h in enumerate(header)]
    out, group, first, length = [], [], None, 0
    for n, values in rows[1:]:
        line = f"row {n}: " + "; ".join(f"{header[j] if j < len(header) else f'column {j + 1}'}: {v}"
                                         for j, v in enumerate(values) if v)
        if group and length + len(line) > size:
            out.append((f"{name}!rows {first}-{last}", "\n".join(group)))
            group, length = [], 0
        if not group:
            first = n
        group.append(line)
        length += len(line) + 1
        last = n
    if group:
        out.append((f"{name}!rows {first}-{last}", "\n".join(group)))
    if not out:     # a header-only sheet is still knowledge (a data dictionary, for example)
        out.append((f"{name}!row {rows[0][0]}", "columns: " + "; ".join(header)))
    return out, []


def extract(path: Path, cfg: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """(locator, text) passages of one file, plus warnings (scanned pages, unreadable sheets)."""
    size, overlap, suffix = cfg["chunk_chars"], cfg["overlap"], path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        out, empty = [], []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if len(text.strip()) < 20:
                empty.append(i)
                continue
            out += _numbered(f"p.{i}", split(text, size, overlap))
        warnings = [f"{len(empty)} page(s) with no text layer (scanned? OCR them first): {empty[:10]}"] if empty else []
        return out, warnings
    if suffix in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(str(path), read_only=True, data_only=True)   # data_only: cached values, not formulas
        out = []
        for ws in wb.worksheets:
            passages, _ = _table(ws.title, [(n, list(r)) for n, r in enumerate(ws.iter_rows(values_only=True), 1)], size)
            out += passages
        wb.close()
        return out, []
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
            rows = list(enumerate(csv.reader(fh), 1))
        return _table(path.stem, rows, size)
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for i, section in enumerate(re.split(r"(?m)^(?=#{1,3} )", text)):
        out += _numbered(f"§{i}", split(section, size, overlap))
    return out, []


def _passages(path: Path, cfg: dict) -> tuple[list[dict], list[dict], list[str]]:
    source = rel(path)
    try:
        raw, warnings = extract(path, cfg)
    except ImportError:
        raise
    except Exception as exc:          # a corrupt or password-protected file must not stop the whole build
        return [], [], [f"could not read: {type(exc).__name__}: {str(exc)[:120]}"]
    chunks, excluded = [], []
    for locator, text in raw:
        verdict = screen(text)
        if verdict:
            excluded.append({"source": source, "locator": locator, "reason": verdict[0], "types": verdict[1]})
            continue
        chunks.append({"id": f"kb:{source}#{locator}", "source": source, "locator": locator,
                       "title": f"{path.name}, {locator}", "text": text,
                       "embed": f"{path.stem.replace('_', ' ').replace('-', ' ')} ({locator}): {text}"})
    return chunks, excluded, warnings


# --------------------------------------------------------------------------- build / freshness


def _paths():
    return KB_DIR / "meta.json", KB_DIR / "chunks.jsonl", KB_DIR / "vectors.npy", KB_DIR / "index.faiss"


def freshness() -> dict:
    """Content-based; reads hashes only (no parsing, no model). `absent` = no sources and no index: nothing to do."""
    files = {rel(p): file_digest(p) for p in sources()}
    meta_path, chunks_path, _, _ = _paths()
    if not meta_path.exists() or not chunks_path.exists():
        return {"state": "absent"} if not files else {"state": "missing", "sources": len(files)}
    meta = load_json(meta_path)
    built = meta.get("sources", {})
    diff = {"new": sorted(set(files) - set(built)), "removed": sorted(set(built) - set(files)),
            "changed": sorted(f for f in set(files) & set(built) if files[f] != built[f])}
    cfg = settings()
    reasons = []
    if meta.get("settings_digest") != settings_digest(cfg):
        reasons.append("chunking settings, safety screen or knowledge-base version changed")
    if meta.get("model") != cfg["model"]:
        reasons.append(f"model {meta.get('model')} -> {cfg['model']}")
    stale = bool(reasons) or any(diff.values())
    out = {"state": "stale" if stale else "fresh", "sources": len(files), **{k: len(v) for k, v in diff.items()},
           "examples": (diff["changed"] + diff["new"] + diff["removed"])[:5]}
    if reasons:
        out["reasons"] = reasons
    return out


def build(full: bool = False) -> dict:
    """Re-extract only files whose bytes changed; re-embed only passages whose text changed; drop removed files."""
    import numpy as np
    import semantic_index
    cfg = settings()
    digest = settings_digest(cfg)
    meta_path, chunks_path, vec_path, index_path = _paths()
    old_meta, old_chunks, cached = {}, [], {}
    if meta_path.exists() and chunks_path.exists():
        old_meta = load_json(meta_path)
        chunk_bytes = chunks_path.read_bytes()
        vec_bytes = vec_path.read_bytes() if vec_path.exists() else b""
        old_chunks = [json.loads(line) for line in chunk_bytes.decode("utf-8").splitlines()]
        trusted = old_meta.get("chunks_sha") == semantic_index._sha(chunk_bytes) and \
            old_meta.get("vectors_sha") == semantic_index._sha(vec_bytes)
        if not trusted:
            print("warning: knowledge-base files are from different builds; re-extracting and re-embedding everything")
            old_meta, old_chunks = {}, []
        elif not full and old_meta.get("model") == cfg["model"] and vec_bytes:
            vectors = np.load(io.BytesIO(vec_bytes))
            cached = {c["hash"]: vectors[i] for i, c in enumerate(old_chunks) if i < len(vectors)}
    reuse = not full and old_meta.get("settings_digest") == digest
    by_source: dict[str, list[dict]] = {}
    for c in old_chunks:
        by_source.setdefault(c["source"], []).append(c)
    old_excluded = {}
    for e in old_meta.get("excluded", []):
        old_excluded.setdefault(e["source"], []).append(e)
    old_warnings = old_meta.get("warnings", {})

    chunks, excluded, warnings, hashes, extracted = [], [], {}, {}, []
    for path in sources():
        source, h = rel(path), file_digest(path)
        hashes[source] = h
        if reuse and old_meta.get("sources", {}).get(source) == h:
            chunks += by_source.get(source, [])
            excluded += old_excluded.get(source, [])
            if source in old_warnings:
                warnings[source] = old_warnings[source]
            continue
        extracted.append(source)
        c, e, w = _passages(path, cfg)
        chunks += c
        excluded += e
        if w:
            warnings[source] = w
    seen = Counter(c["id"] for c in chunks)
    for c in chunks:
        c["hash"] = semantic_index._text_hash(c["embed"])
    todo = [c for c in chunks if c["hash"] not in cached]
    if todo:
        fresh = semantic_index.model(cfg["model"]).encode([c["embed"] for c in todo], normalize_embeddings=True,
                                                          batch_size=32, show_progress_bar=False)
        for c, vec in zip(todo, fresh):
            cached[c["hash"]] = np.asarray(vec, dtype="float32")
    chunk_bytes = "".join(json.dumps(c) + "\n" for c in chunks).encode("utf-8")
    buf = io.BytesIO()
    vectors = np.asarray([cached[c["hash"]] for c in chunks], dtype="float32")
    np.save(buf, vectors)
    vec_bytes = buf.getvalue()
    index_bytes = b""
    if chunks:
        import faiss
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        index_bytes = faiss.serialize_index(index).tobytes()
    # data files first, meta last: until meta is replaced, readers see the old checksums and retry
    write_atomic(chunks_path, chunk_bytes)
    write_atomic(vec_path, vec_bytes)
    write_atomic(index_path, index_bytes)
    old_ids = {c["id"] for c in old_chunks}
    meta = {"kb_version": KB_VERSION, "model": cfg["model"], "settings_digest": digest,
            "documents": len(chunks), "sources": hashes, "extracted_now": extracted,
            "embedded_now": len(todo), "reused": len(chunks) - len(todo),
            "removed": len(old_ids - {c["id"] for c in chunks}),
            "duplicate_ids": sorted(i for i, n in seen.items() if n > 1),
            "excluded": excluded, "warnings": warnings, "commit": head_commit(),
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "chunks_sha": semantic_index._sha(chunk_bytes), "vectors_sha": semantic_index._sha(vec_bytes),
            "index_sha": semantic_index._sha(index_bytes)}
    write_atomic(meta_path, json.dumps(meta, indent=2))
    _loaded.cache_clear()
    return meta


# --------------------------------------------------------------------------- search


class IndexInconsistent(RuntimeError):
    """chunks.jsonl / index.faiss / meta.json do not belong to the same build (mid-refresh, or a crashed build)."""


def available() -> bool:
    meta_path = _paths()[0]
    return meta_path.exists() and load_json(meta_path).get("documents", 0) > 0


def _read_consistent():
    import faiss
    import numpy as np
    import semantic_index
    meta_path, chunks_path, _, index_path = _paths()
    for attempt in range(4):
        meta_text = meta_path.read_text(encoding="utf-8")
        chunk_bytes, index_bytes = chunks_path.read_bytes(), index_path.read_bytes()
        meta = json.loads(meta_text)
        chunks = [json.loads(line) for line in chunk_bytes.decode("utf-8").splitlines()]
        ok = (meta_path.read_text(encoding="utf-8") == meta_text and meta.get("documents") == len(chunks)
              and meta.get("chunks_sha") == semantic_index._sha(chunk_bytes)
              and meta.get("index_sha") == semantic_index._sha(index_bytes))
        if ok:
            index = faiss.deserialize_index(np.frombuffer(index_bytes, dtype="uint8"))
            if index.ntotal == len(chunks):
                return index, chunks, meta
        time.sleep(0.5 * (attempt + 1))
    raise IndexInconsistent(f"knowledge-base files in {rel(KB_DIR)}/ do not match each other (a refresh is running "
                            "or a build crashed); run `python tools/context/refresh.py --stale`")


@lru_cache
def _loaded():
    import semantic_index
    index, chunks, meta = _read_consistent()
    return index, chunks, meta, semantic_index.BM25([c["embed"] for c in chunks])


def index_info() -> dict:
    """What a search ran against (recorded in the manifest's `retrieval.knowledge_base`)."""
    _, chunks, meta, _ = _loaded()
    return {"index": rel(KB_DIR), "model": meta["model"], "passages": len(chunks)}


def search(query: str, k: int | None = None, expansions: list[str] | None = None, source: str | None = None,
           min_dense: float | None = None) -> list[dict]:
    """Hybrid search; each hit carries its citation (source file + locator) and the full passage text."""
    import numpy as np
    import semantic_index
    cfg = settings()
    k = k or cfg["top_k"]
    index, chunks, meta, bm25 = _loaded()
    queries = [query] + [e for e in (expansions or []) if e.strip()]
    vectors = semantic_index.model(meta["model"]).encode([cfg["query_prefix"] + q for q in queries],
                                                         normalize_embeddings=True)
    fused = [0.0] * len(chunks)
    dense = [0.0] * len(chunks)
    lexical = [0.0] * len(chunks)
    for q, vec in zip(queries, vectors):
        scores, ids = index.search(np.asarray([vec], dtype="float32"), len(chunks))
        for r, (i, v) in enumerate(zip(ids[0], scores[0])):
            fused[int(i)] += 1 / (60 + r)
            dense[int(i)] = max(dense[int(i)], float(v))
        qlex = bm25.scores(q)
        for r, i in enumerate(sorted(range(len(chunks)), key=lambda i: qlex[i], reverse=True)):
            if qlex[i] <= 0:
                break
            fused[i] += 1 / (60 + r)
            lexical[i] = max(lexical[i], qlex[i])
    hits = []
    for i in sorted(range(len(chunks)), key=lambda i: fused[i], reverse=True):
        c = chunks[i]
        if source and not fnmatch(c["source"], source) and not fnmatch(Path(c["source"]).name, source):
            continue
        if min_dense is not None and dense[i] < min_dense:
            continue
        hits.append({"citation": f"{c['source']}#{c['locator']}", "source": c["source"], "locator": c["locator"],
                     "dense": round(dense[i], 3), "bm25": round(lexical[i], 2),
                     "fused": round(fused[i] * 1000 / len(queries), 2), "text": c["text"]})
        if len(hits) >= k:
            break
    return hits


# --------------------------------------------------------------------------- CLI


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--full", action="store_true", help="re-extract and re-embed every source")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int)
    s.add_argument("--expand", action="append", default=[], help="extra phrasing of the question (repeatable)")
    s.add_argument("--source", help="only files matching this glob, e.g. 'knowledge/policies/*' or '*.xlsx'")
    s.add_argument("--json", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "build":
        meta = build(full=args.full)
        kinds = dict(Counter(e["reason"] for e in meta["excluded"]))
        print(f"knowledge base: {meta['documents']} passages from {len(meta['sources'])} file(s) "
              f"({len(meta['extracted_now'])} extracted, {meta['embedded_now']} embedded, {meta['reused']} reused, "
              f"{meta['removed']} removed); excluded {kinds or 0} -> {rel(KB_DIR)}/")
        for source, warns in meta["warnings"].items():
            for w in warns:
                print(f"  warning {source}: {w}")
        return 0
    if args.cmd == "status":
        print(json.dumps(freshness(), indent=2))
        meta_path = _paths()[0]
        if meta_path.exists():
            meta = load_json(meta_path)
            for e in meta.get("excluded", []):
                print(f"  excluded [{e['reason']}] {e['source']}#{e['locator']}: {', '.join(e['types'])}")
            for source, warns in meta.get("warnings", {}).items():
                for w in warns:
                    print(f"  warning {source}: {w}")
        return 0
    if not available():
        raise SystemExit(f"no knowledge base; put documents under {', '.join(rel(r) for r in kb_roots())}/ and run: "
                         "python tools/context/knowledge_base.py build")
    hits = search(args.query, k=args.k, expansions=args.expand, source=args.source)
    if args.json:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
        return 0
    for h in hits:
        print(f"{h['dense']:.3f} dense {h['bm25']:>6} bm25  [{h['citation']}]")
        print("    " + h["text"][:400].replace("\n", "\n    ") + (" ..." if len(h["text"]) > 400 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
