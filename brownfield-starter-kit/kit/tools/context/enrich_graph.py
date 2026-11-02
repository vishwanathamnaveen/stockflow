"""Enrich graphify graph.json nodes with code facts graphify does not store.

    python tools/context/enrich_graph.py              # every service + the shared library + overall graph
    python tools/context/enrich_graph.py orders       # one target

graphify (open-source, AST mode) stores per node: id, label, source_file, source_location (start line),
community. Docstrings become separate "rationale" nodes, and there are no signatures, end lines, bodies or
embeddings. This step adds, on every code node that maps to a symbol of the service's index (any language: see
tools/context/common.py and the language adapters):

  qualname, kind, language, signature, docstring, decorators, bases, fields (class attrs -> type), start_line,
  end_line, service, route (METHOD path), publishes / handles (event topics), business_rules, tests (per-test
  coverage), line_coverage, summary, embedding_text, content_hash

and graph-level metadata under graph["context_enrichment"]. graphify ignores unknown keys, so explain/query/
path/affected keep working. Re-run after every graphify build (scripts/graphify_all.py does it automatically).

The stamp records what the facts were built from: normalised hashes of the service's source files
(`source_hashes`) and digests of the non-code inputs (`inputs`: business rules, per-test coverage, published topics).
A change to source files needs a graphify rebuild; a change to only `inputs` needs just this step again (seconds,
idempotent).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (COMMON, CONTEXT_ENGINE_VERSION, GRAPHS, ROOT, Symbol, build_config, build_config_hash,  # noqa: E402
                    business_rule_files, business_rule_id_pattern, code_targets, data_digest, handler_topics,
                    head_commit, in_service, load_json, registry, rel, route_of, service_dir, service_prefix,
                    source_hashes, source_state, symbol_index, write_atomic)

BODY_CHARS = 700


def words(identifier: str) -> str:
    """snake_case / CamelCase -> space separated words (helps embedding models)."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier.replace("_", " "))
    return re.sub(r"\s+", " ", spaced).strip().lower()


def business_rules() -> list[dict]:
    """Rows `| BR-nnn | rule | implemented in |` of the business-rule files (brownfield.business_rules.files).
    The implementing service is the first word of the last column when it names a service ("orders `domain.f`");
    otherwise the service whose code defines the cited symbols (single-service repos cite bare class names)."""
    rules = []
    row = re.compile(rf"\|\s*({business_rule_id_pattern()})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")
    for path in business_rule_files():
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = row.match(line)
            if m:
                br, rule, impl = m.groups()
                service = impl.split()[0] if impl.split() and impl.split()[0] in registry() else None
                refs = re.findall(r"`([^`]+)`", impl)
                if service is None and refs:
                    service = _defining_service(refs)
                rules.append({"id": br, "rule": rule, "implemented_in": impl, "service": service, "refs": refs,
                              "source": rel(path)})
    return rules


def _defining_service(refs: list[str]) -> str | None:
    owners = [s for s in registry() if any(symbol_index(s).find(ref) for ref in refs)]
    return owners[0] if len(owners) == 1 else None


def rules_for(sym: Symbol, rules: list[dict], module_doc: str) -> list[dict]:
    out = []
    for rule in rules:
        cited = rule["service"] == sym.service and any(
            ref == sym.label() or ref == sym.qualname or ref.split(".")[-1] == sym.name and
            (ref.count(".") == 0 or ref.split(".")[0] == sym.module) for ref in rule["refs"])
        in_doc = rule["id"] in sym.docstring
        if cited or in_doc:
            out.append({"id": rule["id"], "rule": rule["rule"], "how": "cited in docs/business-rules.md" if cited else "docstring"})
    return out


def _source(sym: Symbol) -> str:
    lines = (ROOT / sym.file).read_text(encoding="utf-8").splitlines()[sym.start - 1:sym.end]
    return "\n".join(lines)


def _coverage(service: str) -> dict:
    path = ROOT / "var" / "quality" / f"{service}-coverage.json"
    if not path.exists():
        return {}
    return {k.replace("\\", "/"): _sorted_contexts(v) for k, v in load_json(path)["files"].items()}


def _sorted_contexts(data):
    """coverage.py lists each line's test contexts (per file, function and class) in run-dependent order; sort them
    so an identical test run yields an identical digest."""
    if isinstance(data, dict):
        return {k: ({line: sorted(tests) for line, tests in v.items()} if k == "contexts" and isinstance(v, dict)
                    else _sorted_contexts(v)) for k, v in data.items()}
    return data


LOCAL_INPUTS = {"coverage"}   # built from git-ignored files: verifiable on the machine that ran the tests, not in CI


def enrichment_inputs(service: str, *, include_local: bool = True) -> dict[str, str | None]:
    """Digests of the non-code inputs whose facts enrichment copies onto nodes. A reworded business rule or a new
    coverage run changes node facts (and embedding text) without touching any .py file."""
    index = symbol_index(service)
    docstrings = " ".join(s.docstring for s in index.symbols)
    rules = [r for r in business_rules() if r["service"] == service or r["id"] in docstrings]
    sg_path = GRAPHS / "service-graph.json"
    edges = load_json(sg_path)["edges"] if sg_path.exists() else []
    publishes = sorted((e["target"], e["symbol"]) for e in edges
                       if e["type"] == "publishes" and e["source"] == service and e.get("symbol"))
    out = {"business_rules": data_digest(rules), "publishes": data_digest(publishes)}
    if include_local:
        coverage = _coverage(service)
        out["coverage"] = data_digest(coverage) if coverage else None
    return out


def enrich_symbol(sym: Symbol, ctx: dict) -> dict:
    route = route_of(sym)
    publishes = sorted({e["target"][6:] for e in ctx["edges"]
                        if e["type"] == "publishes" and e["source"] == sym.service and e.get("symbol") == sym.label()})
    handles = sorted(t for t, h in ctx["handlers"].get(sym.service, {}).items() if h == sym.qualname)
    rules = rules_for(sym, ctx["rules"], ctx["module_docs"].get(sym.file, ""))
    tests, coverage = [], None
    cov = ctx["coverage"].get(sym.service, {})
    base = service_prefix(sym.service)
    data = cov.get(sym.file[len(base):]) if sym.file.startswith(base) else None
    if data:
        ids = set()
        for line, ctxs in data.get("contexts", {}).items():
            if sym.start <= int(line) <= sym.end:
                ids |= {c.split("|")[0] for c in ctxs if c}
        executed = [n for n in data["executed_lines"] if sym.start <= n <= sym.end]
        missing = [n for n in data["missing_lines"] if sym.start <= n <= sym.end]
        tests = sorted(ids)
        coverage = round(len(executed) / (len(executed) + len(missing)), 2) if executed or missing else None

    parts = [f"{sym.kind} {sym.qualname} in the {sym.service} service ({Path(sym.file).name})."]
    if sym.docstring:
        parts.append(sym.docstring.strip().split("\n\n")[0])
    elif ctx["module_docs"].get(sym.file):
        parts.append(f"Module: {ctx['module_docs'][sym.file].strip().splitlines()[0]}")
    if route:
        parts.append(f"HTTP endpoint {route[0]} {route[1]}.")
    if publishes:
        parts.append(f"Publishes events: {', '.join(publishes)}.")
    if handles:
        parts.append(f"Handles events: {', '.join(handles)}.")
    if sym.fields:
        parts.append("Fields: " + ", ".join(f"{k} ({v})" for k, v in sym.fields.items()) + ".")
    for rule in rules:
        parts.append(f"Business rule {rule['id']}: {rule['rule']}")
    summary = " ".join(parts)
    embedding_text = "\n".join([
        summary,
        f"Name: {words(sym.qualname)}. Signature: {sym.signature}",
        f"Code: {_source(sym)[:BODY_CHARS]}",
    ])
    return {
        "qualname": sym.qualname, "kind": sym.kind, "language": sym.language, "service": sym.service,
        "signature": sym.signature, "docstring": sym.docstring, "decorators": sym.decorators,
        "bases": sym.bases, "fields": sym.fields, "start_line": sym.start, "end_line": sym.end,
        "route": f"{route[0]} {route[1]}" if route else None, "publishes": publishes, "handles": handles,
        "business_rules": rules, "tests": tests, "line_coverage": coverage, "is_test": sym.is_test,
        "summary": summary, "embedding_text": embedding_text,
        "content_hash": hashlib.sha1(embedding_text.encode("utf-8")).hexdigest()[:16],
    }


def _service_of(path: str) -> str | None:
    for service in registry():
        if service_prefix(service) and in_service(path, service):
            return service
    if COMMON is not None and path.startswith(rel(COMMON) + "/"):
        return "common"
    root_level = [s for s in registry() if not service_prefix(s)]
    return root_level[0] if root_level else None


def enrich(target: str, ctx: dict) -> dict:
    graph_dir = ROOT if target == "overall" else service_dir(target)
    path = graph_dir / "graphify-out" / "graph.json"
    graph = load_json(path)
    base = "" if target == "overall" else service_prefix(target)
    rationale = {}   # graphify docstring nodes -> text, keyed by the node they explain
    by_id = {n["id"]: n for n in graph["nodes"]}
    for link in graph["links"]:
        if link["relation"] == "rationale_for" and link["source"] in by_id:
            rationale[link["target"]] = by_id[link["source"]]["label"]
    enriched = matched = 0
    for node in graph["nodes"]:
        if node.get("file_type") != "code" or not node.get("source_file"):
            continue
        file = f"{base}{node['source_file']}".replace("\\", "/")
        service = target if target != "overall" else _service_of(file)
        if service is None:
            continue
        index = symbol_index(service)
        sym = index.for_graph_node(file, node)
        if sym is None:
            if file in index.module_docs and node["label"] == Path(file).name:
                node["docstring"] = index.module_docs[file]
                node["kind"] = "module"
                node["service"] = service
            continue
        matched += 1
        node.update(enrich_symbol(sym, ctx))
        if not node["docstring"] and node["id"] in rationale:
            node["docstring"] = rationale[node["id"]]
        enriched += 1
    graph["graph"] = graph.get("graph") or {}
    stamp = {
        "version": CONTEXT_ENGINE_VERSION, "config_hash": build_config_hash(), "build_config": build_config(),
        "tool": "tools/context/enrich_graph.py", "commit": head_commit(), **ctx["source_state"],
        "enriched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "nodes_enriched": enriched,
        "fields": ["qualname", "kind", "language", "service", "signature", "docstring", "decorators", "bases", "fields",
                   "start_line", "end_line", "route", "publishes", "handles", "business_rules", "tests",
                   "line_coverage", "summary", "embedding_text", "content_hash"],
    }
    if target != "overall":   # freshness is checked per service; the overall graph is rebuilt with any of them
        stamp["source_hashes"] = source_hashes(graph_dir)
        stamp["inputs"] = enrichment_inputs(target)
    graph["graph"]["context_enrichment"] = stamp
    write_atomic(path, json.dumps(graph, indent=2))
    code_nodes = sum(1 for n in graph["nodes"] if n.get("file_type") == "code")
    return {"target": target, "code_nodes": code_nodes, "enriched": enriched}


def context() -> dict:
    sg_path = GRAPHS / "service-graph.json"
    edges = load_json(sg_path)["edges"] if sg_path.exists() else []
    services = code_targets()
    module_docs = {}
    for service in services:
        module_docs.update(symbol_index(service).module_docs)
    return {"edges": edges, "rules": business_rules(), "module_docs": module_docs,
            "handlers": {s: handler_topics(s) for s in registry()},
            "coverage": {s: _coverage(s) for s in services}, "source_state": source_state()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="*", help="service names, 'common', 'overall' (default: all)")
    args = parser.parse_args()
    separate = not any(service_dir(t) is not None and service_dir(t).resolve() == ROOT.resolve() for t in code_targets())
    targets = args.targets or code_targets() + (["overall"] if separate else [])
    ctx = context()
    for target in targets:
        if target == "overall" and not separate:
            continue                       # a service at the repo root: its graph is the overall graph
        graph_dir = ROOT if target == "overall" else (COMMON if target == "common" else service_dir(target))
        if not (graph_dir / "graphify-out" / "graph.json").exists():
            print(f"  skip  {target:<13} no graphify-out/graph.json")
            continue
        result = enrich(target, ctx)
        print(f"  OK    {target:<13} enriched {result['enriched']}/{result['code_nodes']} code nodes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
