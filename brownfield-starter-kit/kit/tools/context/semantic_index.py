"""Semantic search over the system graphs: FAISS (dense) + BM25 (lexical), fused with reciprocal rank.

    python tools/context/semantic_index.py build
    python tools/context/semantic_index.py search "prevent overselling during flash sales" -k 8
    python tools/context/semantic_index.py search "email the supplier" --service notification --json

Corpus (one document per item, each linked to the code symbols it resolves to):
  code      enriched graphify nodes (tools/context/enrich_graph.py): summary + signature + body excerpt
  rule      docs/business-rules.md rows          -> the symbols they cite
  api       OpenAPI operations                   -> the route function
  topic     contracts/events.yaml topics         -> publisher + handler symbols
  doc       docs/**/*.md + README sections       -> (knowledge only)
  service   config/services.yaml descriptions    -> (service routing)

Model: sentence-transformers, local CPU (default BAAI/bge-small-en-v1.5, 384-d). Nothing leaves the machine
after the one-time model download. Index files: graphs/semantic/{index.faiss, vectors.npy, docs.jsonl, meta.json}.

Consistency: each file is replaced atomically and meta.json is written last with the SHA1 of the other three, so a
reader can tell a complete index from one caught between writes (it retries, then raises IndexInconsistent rather
than map vector i to the wrong document). Freshness is content-based: the index is stale when the corpus it would
build now (ids + text hashes) differs from docs.jsonl, or the configured model differs — not when a file is newer.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (COMMON, GRAPHS, code_targets, ROOT, brownfield_config, doc_paths, handler_topics, head_commit,  # noqa: E402
                    is_business_rule_file, knowledge_excluded, label_for, load_json, registry, rel, route_of,
                    service_dir, service_prefix, source_state, symbol_index, write_atomic)
from enrich_graph import business_rules, words  # noqa: E402

INDEX_DIR = GRAPHS / "semantic"
DEFAULTS = {"model": "BAAI/bge-small-en-v1.5",
            "query_prefix": "Represent this sentence for searching relevant passages: ",
            "top_k": 8, "min_dense_score": 0.55}
TOKEN = re.compile(r"[a-z0-9]+")
SEED_TYPES = {"code", "rule", "api", "topic"}   # doc/service hits are knowledge, not landing points
STOP = set("the a an and or of to in on for with by is are be it this that from as at into when then than".split())


def settings() -> dict:
    return {**DEFAULTS, **(brownfield_config().get("semantic") or {})}


# --------------------------------------------------------------------------- corpus


def _code_docs() -> list[dict]:
    docs = []
    for service in code_targets():
        path = service_dir(service) / "graphify-out" / "graph.json"
        if not path.exists():
            continue
        for node in load_json(path)["nodes"]:
            if not node.get("embedding_text") or node.get("is_test"):
                continue
            label = label_for(node["source_file"], node["qualname"])
            docs.append({"id": f"code:{service}:{node['id']}", "type": "code", "service": service,
                         "title": f"{service}:{label}", "text": node["embedding_text"],
                         "links": [{"service": service, "symbol": label, "graph_node": node["id"],
                                    "file": f"{service_prefix(service)}{node['source_file']}", "line": node.get("start_line")}]})
    return docs


def _link(service: str, name: str) -> list[dict]:
    if service not in registry():
        return []
    out = []
    for sym in symbol_index(service).find(name):
        if not sym.is_test:
            out.append({"service": service, "symbol": sym.label(), "file": sym.file, "line": sym.start})
    return out


def _rule_docs() -> list[dict]:
    docs = []
    for rule in business_rules():
        links = [l for ref in rule["refs"] for l in _link(rule["service"], ref)] if rule["service"] else []
        docs.append({"id": f"rule:{rule['id']}", "type": "rule", "service": rule["service"],
                     "title": f"{rule['id']} {rule['rule']}",
                     "text": f"Business rule {rule['id']}: {rule['rule']} Implemented in {rule['implemented_in']}.",
                     "links": links})
    return docs


def _api_docs() -> list[dict]:
    sg = load_json(GRAPHS / "service-graph.json")
    docs = []
    for api in sg["apis"]:
        links = []
        for sym in symbol_index(api["service"]).product_symbols():
            route = route_of(sym)
            if route and route[0] == api["method"] and route[1] == api["path"]:
                links.append({"service": api["service"], "symbol": sym.label(), "file": sym.file, "line": sym.start})
        callers = sorted({e["source"] for e in sg["edges"] if e["type"] == "rest" and e["api"] == api["id"]})
        text = (f"{api['service']} service HTTP API {api['method']} {api['path']}: {api['summary']}. "
                f"Operation {words(api['operation_id'] or '')}. Request {api.get('request_schema') or '-'}, "
                f"response {api.get('response_schema') or '-'}." + (f" Called by {', '.join(callers)}." if callers else ""))
        docs.append({"id": f"api:{api['id']}", "type": "api", "service": api["service"], "title": api["id"],
                     "text": text, "links": links})
    return docs


def _topic_docs() -> list[dict]:
    sg = load_json(GRAPHS / "service-graph.json")
    docs = []
    for topic, info in sg["topics"].items():
        links = []
        for e in sg["edges"]:
            if e["type"] == "publishes" and e["target"] == f"topic:{topic}" and e.get("symbol"):
                links += _link(e["source"], e["symbol"])
        for service in registry():
            handler = handler_topics(service).get(topic)
            if handler:
                links += _link(service, handler)
        text = (f"Event {topic} ({words(topic.replace('.', ' '))}) produced by {info['producer']}, consumed by "
                f"{', '.join(info['consumers']) or 'nobody'}. Payload: {json.dumps(info['payload'])}.")
        docs.append({"id": f"topic:{topic}", "type": "topic", "service": info["producer"], "title": topic,
                     "text": text, "links": links})
    return docs


def _doc_docs() -> list[dict]:
    docs = []
    # tooling docs, samples and presenter material (brownfield.knowledge_exclude) are excluded
    files = sorted(set(doc_paths())) + [ROOT / "README.md"]
    for path in files:
        if not path.exists() or knowledge_excluded(path) or is_business_rule_file(path):
            continue
        text = path.read_text(encoding="utf-8")
        for i, section in enumerate(re.split(r"(?m)^(?=#{1,3} )", text)):
            section = section.strip()
            if len(section) < 60:
                continue
            title = section.splitlines()[0].lstrip("# ").strip()
            mentioned = [s for s in registry() if re.search(rf"\b{re.escape(s)}\b", section)]
            docs.append({"id": f"doc:{rel(path)}#{i}", "type": "doc", "service": mentioned[0] if len(mentioned) == 1 else None,
                         "title": f"{rel(path)} — {title}", "text": section[:1500],
                         "links": _identifier_links(section, mentioned)})
    return docs


def _identifier_links(text: str, services: list[str]) -> list[dict]:
    """Code symbols a doc section names in backticks, resolved in the services it mentions (else all)."""
    links, seen = [], set()
    for ident in re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*)`", text):
        for service in services or list(registry()):
            for link in _link(service, ident.rstrip("()")):
                key = (link["service"], link["symbol"])
                if key not in seen:
                    seen.add(key)
                    links.append(link)
    return links[:8]


def _service_docs() -> list[dict]:
    return [{"id": f"service:{name}", "type": "service", "service": name, "title": name,
             "text": f"{name} service: {cfg.get('description', '')} Owner {cfg.get('owner', '')}.", "links": []}
            for name, cfg in registry().items()]


def corpus() -> list[dict]:
    return _code_docs() + _rule_docs() + _api_docs() + _topic_docs() + _doc_docs() + _service_docs()


# --------------------------------------------------------------------------- models


@lru_cache
def model(name: str):
    """Load from the local cache first (no network, works air-gapped); download only on first use."""
    from sentence_transformers import SentenceTransformer  # heavy import: only when needed
    try:
        return SentenceTransformer(name, device="cpu", local_files_only=True)
    except Exception:
        try:  # TLS-inspecting proxy: trust the OS certificate store for the one-time download, as pip >= 24.2 does
            import truststore
            truststore.inject_into_ssl()
        except ImportError:
            pass
        return SentenceTransformer(name, device="cpu")


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN.findall(words(text)) if t not in STOP]


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.docs = [Counter(tokens(t)) for t in texts]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query: str) -> list[float]:
        q = tokens(query)
        out = []
        for d, length in zip(self.docs, self.lengths):
            s = 0.0
            for t in q:
                if t in d:
                    tf = d[t]
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.avg))
            out.append(s)
        return out


# --------------------------------------------------------------------------- build / search


def _text_hash(text: str) -> str:
    import hashlib
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha1(data).hexdigest()


class IndexInconsistent(RuntimeError):
    """index.faiss / docs.jsonl / meta.json do not belong to the same build (mid-refresh, or a crashed build)."""


def _cache_trusted(meta: dict, docs_bytes: bytes, vec_bytes: bytes) -> bool:
    """Reusing vectors by position is only safe when docs.jsonl and vectors.npy come from the same build; a torn
    write would otherwise attach one document's vector to another's hash and poison every later build."""
    if "docs_sha" not in meta:      # built before checksums existed: trust it, as earlier versions did
        return True
    return meta["docs_sha"] == _sha(docs_bytes) and meta.get("vectors_sha") == _sha(vec_bytes)


def freshness() -> dict:
    """Compare the corpus that would be built now with the indexed one (ids + text hashes); no model needed."""
    meta_path, docs_path = INDEX_DIR / "meta.json", INDEX_DIR / "docs.jsonl"
    if not (meta_path.exists() and docs_path.exists() and (INDEX_DIR / "index.faiss").exists()):
        return {"state": "missing"}
    meta = load_json(meta_path)
    indexed = {d["id"]: d.get("hash") for d in map(json.loads, docs_path.read_text(encoding="utf-8").splitlines())}
    now = {d["id"]: _text_hash(d["text"]) for d in corpus()}
    diff = {"new": sorted(set(now) - set(indexed)), "removed": sorted(set(indexed) - set(now)),
            "changed": sorted(i for i in set(now) & set(indexed) if now[i] != indexed[i])}
    model_changed = meta.get("model") != settings()["model"]
    stale = model_changed or any(diff.values())
    out = {"state": "stale" if stale else "fresh", **{k: len(v) for k, v in diff.items()},
           "examples": (diff["changed"] + diff["new"] + diff["removed"])[:5]}
    if model_changed:
        out["model_changed"] = f"{meta.get('model')} -> {settings()['model']}"
    return out


def build(full: bool = False) -> dict:
    """Incremental: vectors of documents whose text is unchanged are reused (vectors.npy + docs.jsonl hashes);
    only new/changed documents are embedded, and the model is not loaded at all when nothing changed. Documents
    whose source disappeared are dropped, because the corpus is regenerated from the current graphs every time."""
    import io

    import faiss
    import numpy as np
    cfg = settings()
    state = source_state()
    docs = corpus()
    for d in docs:
        d["hash"] = _text_hash(d["text"])
    cached: dict[str, np.ndarray] = {}
    old_ids: set[str] = set()
    meta_path, vec_path, docs_path = INDEX_DIR / "meta.json", INDEX_DIR / "vectors.npy", INDEX_DIR / "docs.jsonl"
    if vec_path.exists() and docs_path.exists() and meta_path.exists():
        old_meta = load_json(meta_path)
        docs_bytes, vec_bytes = docs_path.read_bytes(), vec_path.read_bytes()
        old_docs = [json.loads(line) for line in docs_bytes.decode("utf-8").splitlines()]
        old_ids = {d["id"] for d in old_docs}
        trusted = _cache_trusted(old_meta, docs_bytes, vec_bytes)
        if not trusted:
            print("warning: vectors.npy and docs.jsonl are from different builds; re-embedding everything")
        if not full and trusted and old_meta.get("model") == cfg["model"]:
            old_vectors = np.load(io.BytesIO(vec_bytes))
            for i, old in enumerate(old_docs):
                if old.get("hash") and i < len(old_vectors):
                    cached[old["hash"]] = old_vectors[i]
    todo = [d for d in docs if d["hash"] not in cached]
    if todo:
        fresh = model(cfg["model"]).encode([d["text"] for d in todo], normalize_embeddings=True,
                                           batch_size=32, show_progress_bar=False)
        for d, vec in zip(todo, fresh):
            cached[d["hash"]] = np.asarray(vec, dtype="float32")
    vectors = np.asarray([cached[d["hash"]] for d in docs], dtype="float32")
    index = faiss.IndexFlatIP(vectors.shape[1])   # exact cosine (vectors are normalised); fine below ~1M docs
    index.add(vectors)
    index_bytes = faiss.serialize_index(index).tobytes()
    buf = io.BytesIO()
    np.save(buf, vectors)
    vec_bytes = buf.getvalue()
    docs_bytes = "".join(json.dumps(d) + "\n" for d in docs).encode("utf-8")
    # data files first, meta last: until meta is replaced, readers see the old checksums and retry
    write_atomic(docs_path, docs_bytes)
    write_atomic(vec_path, vec_bytes)
    write_atomic(INDEX_DIR / "index.faiss", index_bytes)
    meta = {"model": cfg["model"], "dim": int(vectors.shape[1]), "documents": len(docs),
            "embedded_now": len(todo), "reused": len(docs) - len(todo),
            "removed": len(old_ids - {d["id"] for d in docs}),
            "by_type": dict(Counter(d["type"] for d in docs)), "commit": head_commit(), **state,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "docs_sha": _sha(docs_bytes), "vectors_sha": _sha(vec_bytes), "index_sha": _sha(index_bytes)}
    write_atomic(meta_path, json.dumps(meta, indent=2))
    _loaded.cache_clear()
    return meta


def _read_consistent():
    import faiss
    import numpy as np
    meta_path = INDEX_DIR / "meta.json"
    for attempt in range(4):
        meta_text = meta_path.read_text(encoding="utf-8")
        docs_bytes = (INDEX_DIR / "docs.jsonl").read_bytes()
        index_bytes = (INDEX_DIR / "index.faiss").read_bytes()
        meta = json.loads(meta_text)
        docs = [json.loads(line) for line in docs_bytes.decode("utf-8").splitlines()]
        index = faiss.deserialize_index(np.frombuffer(index_bytes, dtype="uint8"))
        consistent = (meta_path.read_text(encoding="utf-8") == meta_text          # no rebuild landed mid-read
                      and index.ntotal == len(docs) == meta.get("documents", len(docs))
                      and ("docs_sha" not in meta or (meta["docs_sha"] == _sha(docs_bytes)
                                                      and meta.get("index_sha") == _sha(index_bytes))))
        if consistent:
            return index, docs, meta
        time.sleep(0.5 * (attempt + 1))
    raise IndexInconsistent(f"semantic index files in {rel(INDEX_DIR)}/ do not match each other (a refresh is "
                            "running or a build crashed); run `python tools/context/refresh.py --stale`")


@lru_cache
def _loaded():
    index, docs, meta = _read_consistent()
    return index, docs, meta, BM25([d["text"] for d in docs])


def available() -> bool:
    # meta.json is written last, so an interrupted first build leaves index.faiss without it
    return (INDEX_DIR / "index.faiss").exists() and (INDEX_DIR / "meta.json").exists()


def search(query: str, k: int | None = None, service: str | None = None, types: set[str] | None = None,
           expansions: list[str] | None = None) -> list[dict]:
    """Hybrid search. `expansions` are extra phrasings of the task in code/domain terms (from the builder agent);
    each query is scored dense + BM25 and every ranking is fused with reciprocal rank (k=60)."""
    import numpy as np
    cfg = settings()
    k = k or cfg["top_k"]
    index, docs, meta, bm25 = _loaded()
    queries = [query] + [e for e in (expansions or []) if e.strip()]
    vectors = model(meta["model"]).encode([cfg["query_prefix"] + q for q in queries], normalize_embeddings=True)
    fused: dict[int, float] = {i: 0.0 for i in range(len(docs))}
    dense: dict[int, float] = {i: 0.0 for i in range(len(docs))}
    lexical = [0.0] * len(docs)
    for q, vec in zip(queries, vectors):
        scores, ids = index.search(np.asarray([vec], dtype="float32"), len(docs))
        qdense = {int(i): float(v) for i, v in zip(ids[0], scores[0])}
        qlex = bm25.scores(q)
        for r, i in enumerate(sorted(qdense, key=qdense.get, reverse=True)):
            fused[i] += 1 / (60 + r)
            dense[i] = max(dense[i], qdense[i])
        for r, i in enumerate(sorted(range(len(docs)), key=lambda i: qlex[i], reverse=True)):
            if qlex[i] <= 0:
                break
            fused[i] += 1 / (60 + r)
            lexical[i] = max(lexical[i], qlex[i])
    hits = []
    for i in sorted(fused, key=fused.get, reverse=True):
        d = docs[i]
        if service and d["service"] not in (service, None):
            continue
        if types and d["type"] not in types:
            continue
        hits.append({"id": d["id"], "type": d["type"], "service": d["service"], "title": d["title"],
                     "dense": round(dense[i], 3), "bm25": round(lexical[i], 2), "fused": round(fused[i] * 1000 / len(queries), 2),
                     "links": d["links"]})
        if len(hits) >= k:
            break
    return hits


def seed_search(query: str, k: int = 10, expansions: list[str] | None = None) -> tuple[list[dict], dict]:
    """Code symbols reached by the top hits: direct code hits, or symbols linked from rules/APIs/topics/docs.
    Also returns the retrieval log: the queries sent to FAISS + BM25, the settings, and every hit with its scores
    and what it produced (recorded in the manifest's `retrieval.semantic_index`)."""
    cfg = settings()
    out: dict[str, dict] = {}
    log = []
    for rank, hit in enumerate(search(query, k=k, expansions=expansions, types=SEED_TYPES)):
        entry = {"rank": rank + 1, "id": hit["id"], "type": hit["type"], "service": hit["service"],
                 "title": hit["title"][:100], "dense": hit["dense"], "bm25": hit["bm25"], "fused": hit["fused"]}
        if hit["dense"] < cfg["min_dense_score"]:
            log.append({**entry, "outcome": "dropped: below min_dense_score"})
            continue
        added = []
        for link in hit["links"]:
            key = f"{link['service']}:{link['symbol']}"
            if key not in out:
                out[key] = {"service": link["service"], "symbol": link["symbol"], "file": link.get("file"),
                            "score": hit["dense"], "rank": rank, "via": f"{hit['type']} {hit['title'][:70]}"}
                added.append(key)
        outcome = "candidate" if added else ("already a candidate" if hit["links"] else "no linked code")
        log.append({**entry, "outcome": outcome, "candidates": added})
    _, docs, meta, _ = _loaded()
    trace = {"index": rel(INDEX_DIR), "model": meta["model"], "documents": len(docs),
             "query_prefix": cfg["query_prefix"],
             "queries": [{"role": "task", "text": query}]
                        + [{"role": "expansion", "text": e} for e in (expansions or []) if e.strip()],
             "search": {"k": k, "types": sorted(SEED_TYPES), "min_dense_score": cfg["min_dense_score"],
                        "fusion": "FAISS cosine + BM25 per query, RRF k=60"},
             "hits": log}
    return sorted(out.values(), key=lambda c: (c["rank"], -c["score"])), trace


def seed_candidates(query: str, k: int = 10, expansions: list[str] | None = None) -> list[dict]:
    return seed_search(query, k=k, expansions=expansions)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--full", action="store_true", help="re-embed every document (e.g. after changing the model)")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=8)
    s.add_argument("--service")
    s.add_argument("--type", action="append", choices=["code", "rule", "api", "topic", "doc", "service"])
    s.add_argument("--json", action="store_true")
    s.add_argument("--seeds", action="store_true", help="show resolved code seed candidates instead of raw hits")
    s.add_argument("--expand", action="append", default=[],
                   help="extra phrasing in code/domain terms (repeatable), e.g. --expand 'supplier email purchase order submitted'")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "build":
        meta = build(full=args.full)
        print(f"semantic index: {meta['documents']} docs ({meta['embedded_now']} embedded, {meta['reused']} reused, "
              f"{meta['removed']} removed) "
              f"{meta['by_type']} model={meta['model']} dim={meta['dim']} -> {rel(INDEX_DIR)}/")
        return 0
    if not available():
        raise SystemExit("no index; run: python tools/context/semantic_index.py build")
    if args.seeds:
        rows = seed_candidates(args.query, k=args.k, expansions=args.expand)
        if args.json:
            print(json.dumps(rows, indent=2))
        else:
            for r in rows:
                print(f"{r['score']:.3f}  {r['service']}:{r['symbol']:<40} via {r['via']}")
        return 0
    hits = search(args.query, k=args.k, service=args.service, types=set(args.type) if args.type else None,
                  expansions=args.expand)
    if args.json:
        print(json.dumps(hits, indent=2))
    else:
        for h in hits:
            links = ", ".join(f"{l['service']}:{l['symbol']}" for l in h["links"][:3])
            print(f"{h['dense']:.3f} dense  {h['bm25']:>5} bm25  [{h['type']:<7}] {h['title'][:70]}" + (f"  -> {links}" if links else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
