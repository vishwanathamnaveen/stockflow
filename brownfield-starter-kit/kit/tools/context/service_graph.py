"""Build the service graph: services, APIs, topics and how they connect.

    python tools/context/service_graph.py            # writes graphs/service-graph.json + graphs/SERVICE_GRAPH.md

Sources (each edge records which ones confirm it):
  config    config/services.yaml, config/subscriptions.yaml (optional), gateway routes.py (optional)
  contract  contracts/openapi/<service>.json|yaml, contracts/events.yaml
  static    the service's code, read through its convention presets (tools/context/conventions.py): REST clients
            (ServiceClient, Feign, RestTemplate / WebClient, HttpClient, axios, ...), event publication
            (publish_event, KafkaTemplate / RabbitTemplate / StreamBridge, emit, ...) and event handlers
            (HANDLERS dict, @KafkaListener / @RabbitListener / @JmsListener, @EventPattern, ...)
  runtime   var/traces/<service>.jsonl (CLIENT spans with peer.service, CONSUMER spans)

Consistency checks between these sources are written to `checks`; the context
manifest surfaces the ones that touch a task as conflicts.

Freshness: `inputs_digest` hashes the config, contract and service source files above. Traces are excluded on
purpose: runtime evidence proves presence only, so new traffic is picked up on the next refresh but never makes the
graph "stale".
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (GRAPHS, ROOT, TRACES, brownfield_config, files_digest, handler_topics, head_commit, load_json,  # noqa: E402
                    load_openapi, load_yaml, openapi_file, openapi_path_regex, package_dir, publishers, registry,
                    rel, rest_calls, service_dir, service_excludes, source_files, source_state, symbol_index,
                    write_atomic)

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
DEFAULT_OPS_PATHS = ["/health"]


def ops_paths() -> set[str]:
    """Operational endpoints left out of the API list (brownfield.service_graph.ops_paths)."""
    return set((brownfield_config().get("service_graph") or {}).get("ops_paths") or DEFAULT_OPS_PATHS)


def code_apis(service: str) -> list[dict]:
    """APIs of a service without an OpenAPI contract: the HTTP routes its code declares (convention presets), with
    request / response types from the route signatures. Marked source: code, so a reader knows no contract backs
    them (contract-shape checks are weaker than with a real OpenAPI file)."""
    import conventions
    index = symbol_index(service)
    apis, seen = [], set()
    for sym in index.product_symbols():
        if not sym.route:
            continue
        method, path = sym.route
        api_id = f"{service}:{method} {path}"
        if api_id in seen or path in ops_paths():
            continue
        seen.add(api_id)
        header = "\n".join(index.texts.get(sym.file, "").splitlines()[sym.start - 1:sym.end])
        apis.append({"id": api_id, "service": service, "method": method, "path": path, "operation_id": sym.qualname,
                     "summary": (sym.docstring.strip().splitlines() or [""])[0][:120],
                     "request_schema": conventions.request_type(header, index.conventions, ROOT),
                     "response_schema": conventions.response_type(sym.signature, sym.name),
                     "source": "code", "location": f"{sym.file}:{sym.start}"})
    return apis


def _apis() -> list[dict]:
    apis = []
    skip = ops_paths()
    for service in registry():
        path = openapi_file(service)
        if path is None:
            apis += code_apis(service)
            continue
        for api_path, ops in (load_openapi(path).get("paths") or {}).items():
            for method, op in ops.items():
                if method not in HTTP_METHODS or api_path in skip or not isinstance(op, dict):
                    continue
                apis.append({
                    "id": f"{service}:{method.upper()} {api_path}", "service": service, "method": method.upper(),
                    "path": api_path, "operation_id": op.get("operationId"), "summary": op.get("summary", ""),
                    "request_schema": _schema_ref(op.get("requestBody", {})),
                    "response_schema": _schema_ref(op.get("responses", {}).get(next(iter(op.get("responses", {"": 0})), ""), {})),
                })
    return apis


def _schema_ref(block: dict) -> str | None:
    text = json.dumps(block)
    m = re.search(r'#/components/schemas/([A-Za-z0-9_]+)', text)
    return m.group(1) if m else None


def load_event_catalogue() -> tuple[dict, list[dict]]:
    """contracts/events.yaml topics; tolerates `type?` optional markers that strict YAML rejects."""
    path = ROOT / "contracts" / "events.yaml"
    if not path.exists():
        return {}, []
    text = path.read_text(encoding="utf-8")
    try:
        return (yaml.safe_load(text) or {}).get("topics", {}) or {}, []
    except yaml.YAMLError as exc:
        lenient = re.sub(r"(?<=:)(\s*)([A-Za-z_\[\]]+\?)(?=\s*[,}\]])", lambda m: f'{m.group(1)}"{m.group(2)}"', text)
        check = {"severity": "warning", "kind": "event_catalogue_not_strict_yaml", "topics": [],
                 "message": f"contracts/events.yaml is not valid YAML ({str(exc).splitlines()[0]}); "
                            "optional markers like `str?` inside {...} must be quoted",
                 "evidence": rel(path)}
        return (yaml.safe_load(lenient) or {}).get("topics", {}) or {}, [check]


def match_api(apis: list[dict], service: str, method: str, path: str) -> dict | None:
    """The contract operation a call / route stands for. Method ANY (net/http HandleFunc, RestTemplate.exchange)
    matches any method of the path."""
    candidates = [a for a in apis if a["service"] == service and (method == "ANY" or a["method"] == method)]
    exact = [a for a in candidates if a["path"] == path]
    if exact:
        return exact[0]
    for api in sorted(candidates, key=lambda a: a["path"].count("{")):
        if openapi_path_regex(api["path"]).match(path):
            return api
    return None


def _rest_calls(service: str) -> list[dict]:
    return rest_calls(service)


def _publishers(service: str) -> list[dict]:
    return publishers(service)


def _gateway_routes() -> dict[str, str]:
    """ROUTES of an API gateway service named "gateway" (Python routes.py), when the repo has one."""
    if "gateway" not in registry() or not (package_dir("gateway") / "routes.py").exists():
        return {}
    path = package_dir("gateway") / "routes.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if getattr(target, "id", None) == "ROUTES":
                return ast.literal_eval(node.value)
    return {}


def _runtime(apis: list[dict]) -> tuple[Counter, dict, Counter, list[dict]]:
    """Observed REST calls and event consumption from trace files."""
    rest, samples, consumed, unmatched = Counter(), {}, Counter(), []
    if not TRACES.exists():
        return rest, samples, consumed, unmatched
    ports = {cfg["port"]: name for name, cfg in registry().items() if cfg.get("port")}
    for trace in TRACES.glob("*.jsonl"):
        for line in trace.open(encoding="utf-8"):
            try:
                span = json.loads(line)
            except json.JSONDecodeError:
                continue
            attrs, caller = span.get("attributes", {}), span.get("service")
            if span.get("kind") == "CLIENT" and attrs.get("http.url"):
                url = urlparse(attrs["http.url"])
                target = attrs.get("peer.service") or ports.get(url.port)
                if not target or target == "event-bus" or caller == "gateway":
                    continue   # bus deliveries and gateway proxying are modelled as edges of their own
                api = match_api(apis, target, attrs.get("http.method", span.get("name", "")).upper(), url.path)
                if api:
                    rest[(caller, api["id"])] += 1
                    samples.setdefault((caller, api["id"]), span["trace_id"])
                elif not url.path.startswith("/events"):
                    unmatched.append({"caller": caller, "target": target, "path": url.path})
            elif span.get("kind") == "CONSUMER" and span.get("name", "").endswith(" process"):
                topic = span["name"].rsplit(" ", 1)[0]
                consumed[(topic, caller)] += 1
                samples.setdefault((topic, caller), span["trace_id"])
    return rest, samples, consumed, unmatched


def input_files() -> list[Path]:
    files = [ROOT / "config" / "services.yaml", ROOT / "config" / "subscriptions.yaml", ROOT / "contracts" / "events.yaml",
             ROOT / "config" / "conventions.yaml"]
    files += sorted(p for suffix in ("json", "yaml", "yml") for p in (ROOT / "contracts" / "openapi").glob(f"*.{suffix}"))
    files += [ROOT / (registry()[s].get("openapi")) for s in registry() if registry()[s].get("openapi")]
    for service in registry():
        files += source_files(service_dir(service), exclude=service_excludes(service))
    return list(dict.fromkeys(files))


def inputs_digest() -> str:
    return files_digest(input_files())


def freshness() -> dict:
    path = GRAPHS / "service-graph.json"
    if not path.exists():
        return {"state": "missing"}
    graph = load_json(path)
    recorded = graph.get("inputs_digest")
    state = "fresh" if recorded == inputs_digest() else "stale"
    out = {"state": state, "built_at_commit": graph.get("built_at_commit")}
    if recorded is None:
        out["reason"] = "built before input digests were recorded; rebuild"
    return out


def build() -> dict:
    services = registry()
    digest = inputs_digest()   # taken before reading: an edit during the build leaves the graph stale, not wrong-fresh
    apis = _apis()
    events, catalogue_checks = load_event_catalogue()
    sub_path = ROOT / "config" / "subscriptions.yaml"
    subscriptions = (load_yaml(sub_path).get("subscriptions") or {}) if sub_path.exists() else {}
    # Routing is declared in config only in repos with a broker-routing file; elsewhere (Kafka, RabbitMQ, SQS
    # listeners) the handler annotation *is* the subscription, so "not routed" checks would only be noise.
    routing_declared = bool(subscriptions)
    runtime_rest, samples, runtime_consumed, runtime_unmatched = _runtime(apis)
    edges, checks = [], list(catalogue_checks)

    for prefix, target in _gateway_routes().items():
        edges.append({"type": "gateway_route", "source": "gateway", "target": target,
                      "prefix": f"/api/{prefix}", "evidence": ["config"]})

    static_rest = set()
    for service in services:
        for call in _rest_calls(service):
            api = match_api(apis, call["target"], call["method"], call["path"])
            if api is None:
                checks.append({"severity": "error", "kind": "client_path_not_in_contract", "services": [service, call["target"]],
                               "message": f"{service} {call['client']} calls {call['method']} {call['path']} on {call['target']}, "
                                          f"not in {rel(openapi_file(call['target'])) if openapi_file(call['target']) else 'its OpenAPI contract (none found)'}",
                               "evidence": f"{call['file']}:{call['line']}"})
                continue
            key = (service, api["id"])
            static_rest.add(key)
            edge = {"type": "rest", "source": service, "target": call["target"], "api": api["id"],
                    "client": call["client"], "evidence": ["static", "contract"], "location": f"{call['file']}:{call['line']}"}
            if runtime_rest.get(key):
                edge["evidence"].append("runtime")
                edge["runtime"] = {"calls": runtime_rest[key], "sample_trace": samples[key]}
            edges.append(edge)
    for (caller, api_id), count in runtime_rest.items():
        if (caller, api_id) not in static_rest:
            checks.append({"severity": "warning", "kind": "runtime_call_without_static_client", "services": [caller, api_id.split(":")[0]],
                           "message": f"runtime shows {caller} calling {api_id} ({count}x) but no client code was found",
                           "evidence": samples[(caller, api_id)]})
    for item in runtime_unmatched[:10]:
        checks.append({"severity": "warning", "kind": "runtime_call_not_in_contract", "services": [item["caller"], item["target"]],
                       "message": f"runtime call {item['caller']} -> {item['target']} {item['path']} matches no OpenAPI path"})

    code_publishers: dict[str, list[dict]] = defaultdict(list)
    for service in services:
        for pub in _publishers(service):
            code_publishers[pub["topic"]].append({**pub, "service": service})
    handlers = {service: handler_topics(service) for service in services}

    for topic in sorted(set(events) | set(code_publishers) | set(subscriptions)):
        declared = events.get(topic, {})
        for pub in code_publishers.get(topic, []):
            evidence = ["static"] + (["contract"] if declared.get("producer") == pub["service"] else [])
            edges.append({"type": "publishes", "source": pub["service"], "target": f"topic:{topic}",
                          "symbol": pub["symbol"], "evidence": evidence, "location": f"{pub['file']}:{pub['line']}"})
            if declared and declared.get("producer") != pub["service"]:
                checks.append({"severity": "warning", "kind": "producer_mismatch", "topics": [topic], "services": [pub["service"]],
                               "message": f"{topic}: code publishes from {pub['service']}, events.yaml says {declared.get('producer')}"})
        if topic not in events:
            checks.append({"severity": "warning", "kind": "topic_not_in_catalogue", "topics": [topic],
                           "message": f"{topic} is published/subscribed but missing from contracts/events.yaml"})
        if declared and not code_publishers.get(topic):
            checks.append({"severity": "info", "kind": "declared_topic_never_published", "topics": [topic],
                           "message": f"{topic} is in events.yaml (producer {declared.get('producer')}) but no publishing code was found"})
        routed = set(subscriptions.get(topic, []))
        declared_consumers = set(declared.get("consumers", []))
        for service in sorted(routed | declared_consumers | {s for s, h in handlers.items() if topic in h}):
            evidence = []
            if service in routed:
                evidence.append("config")
            if service in declared_consumers:
                evidence.append("contract")
            if topic in handlers.get(service, {}):
                evidence.append("static")
            edge = {"type": "consumes", "source": f"topic:{topic}", "target": service,
                    "handler": handlers.get(service, {}).get(topic), "evidence": evidence}
            if runtime_consumed.get((topic, service)):
                edge["evidence"].append("runtime")
                edge["runtime"] = {"deliveries": runtime_consumed[(topic, service)], "sample_trace": samples[(topic, service)]}
            edges.append(edge)
            if service in routed and topic not in handlers.get(service, {}):
                checks.append({"severity": "error", "kind": "subscription_without_handler", "topics": [topic], "services": [service],
                               "message": f"{topic} is routed to {service} but {service} has no handler for it (deliveries will fail)"})
            if routing_declared and topic in handlers.get(service, {}) and service not in routed:
                checks.append({"severity": "warning", "kind": "handler_without_subscription", "topics": [topic], "services": [service],
                               "message": f"{service} handles {topic} but config/subscriptions.yaml does not route it there"})
            if service in routed and service not in declared_consumers:
                checks.append({"severity": "warning", "kind": "consumer_not_in_catalogue", "topics": [topic], "services": [service],
                               "message": f"{topic} is routed to {service} but events.yaml does not list it as a consumer"})
            if routing_declared and service in declared_consumers and service not in routed:
                checks.append({"severity": "warning", "kind": "catalogue_consumer_not_routed", "topics": [topic], "services": [service],
                               "message": f"events.yaml lists {service} as a consumer of {topic} but it is not subscribed"})
        if code_publishers.get(topic) and not routed and (routing_declared or not any(topic in h for h in handlers.values())):
            checks.append({"severity": "info", "kind": "topic_without_subscribers", "topics": [topic],
                           "message": f"{topic} is published but has no subscribers"})

    depends: dict[tuple[str, str], set[str]] = defaultdict(set)
    for edge in edges:
        if edge["type"] == "rest":
            depends[(edge["source"], edge["target"])].add("rest")
    for edge in (e for e in edges if e["type"] == "publishes"):
        for consumer in (e for e in edges if e["type"] == "consumes" and e["source"] == edge["target"]):
            depends[(consumer["target"], edge["source"])].add(f"event:{edge['target'][6:]}")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_at_commit": head_commit(), **source_state(), "inputs_digest": digest,
        "services": {name: {"port": cfg.get("port"), "package": cfg.get("package"), "owner": cfg.get("owner"),
                            "description": cfg.get("description"),
                            "database": cfg.get("database"),
                            "path": rel(service_dir(name)), "languages": sorted(symbol_index(name).languages),
                            "conventions": symbol_index(name).conventions}
                     for name, cfg in services.items()},
        "apis": apis,
        "topics": {name: {"producer": t.get("producer"), "consumers": t.get("consumers", []), "payload": t.get("payload")}
                   for name, t in events.items()},
        "edges": edges,
        "dependencies": [{"consumer": c, "provider": p, "channels": sorted(ch)} for (c, p), ch in sorted(depends.items())],
        "checks": checks,
    }


def render_markdown(graph: dict) -> str:
    lines = ["# Service graph", "", f"Generated {graph['generated_at']} at commit `{graph['built_at_commit']}` by "
             "`tools/context/service_graph.py`. Solid = REST, dotted = event.", "", "```mermaid", "flowchart LR"]
    for edge in graph["edges"]:
        if edge["type"] == "rest":
            lines.append(f"  {edge['source']} -->|{edge['api'].split(':', 1)[1]}| {edge['target']}")
    for dep in graph["dependencies"]:
        for channel in dep["channels"]:
            if channel.startswith("event:"):
                lines.append(f"  {dep['provider']} -.->|{channel[6:]}| {dep['consumer']}")
    lines += ["```", "", "## Service dependencies", "", "| Consumer | Provider | Channels |", "|---|---|---|"]
    lines += [f"| {d['consumer']} | {d['provider']} | {', '.join(d['channels'])} |" for d in graph["dependencies"]]
    lines += ["", "## REST edges", "", "| Caller | Client | API | Evidence | Runtime calls |", "|---|---|---|---|---|"]
    for e in (e for e in graph["edges"] if e["type"] == "rest"):
        lines.append(f"| {e['source']} | `{e['client']}` | `{e['api']}` | {', '.join(e['evidence'])} | "
                     f"{e.get('runtime', {}).get('calls', 0)} |")
    lines += ["", "## Events", "", "| Topic | Publisher (symbol) | Consumer (handler) | Evidence |", "|---|---|---|---|"]
    for e in (e for e in graph["edges"] if e["type"] == "consumes"):
        pubs = [p for p in graph["edges"] if p["type"] == "publishes" and p["target"] == e["source"]]
        pub = ", ".join(f"{p['source']} (`{p['symbol']}`)" for p in pubs) or "—"
        lines.append(f"| `{e['source'][6:]}` | {pub} | {e['target']} (`{e.get('handler')}`) | {', '.join(e['evidence'])} |")
    for p in (p for p in graph["edges"] if p["type"] == "publishes"):
        if not any(e["type"] == "consumes" and e["source"] == p["target"] for e in graph["edges"]):
            lines.append(f"| `{p['target'][6:]}` | {p['source']} (`{p['symbol']}`) | — | {', '.join(p['evidence'])} |")
    lines += ["", "## Consistency checks", ""]
    lines += [f"- **{c['severity']}** `{c['kind']}` — {c['message']}" for c in graph["checks"]] or ["- none"]
    return "\n".join(lines) + "\n"


def main() -> int:
    graph = build()
    write_atomic(GRAPHS / "service-graph.json", json.dumps(graph, indent=2))
    write_atomic(GRAPHS / "SERVICE_GRAPH.md", render_markdown(graph))
    counts = Counter(e["type"] for e in graph["edges"])
    print(f"service graph: {len(graph['services'])} services, {len(graph['apis'])} APIs, {len(graph['topics'])} topics, "
          f"edges {dict(counts)}, {len(graph['checks'])} checks -> {rel(GRAPHS)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
