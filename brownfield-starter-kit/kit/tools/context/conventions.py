"""Framework conventions as data: how a codebase declares HTTP routes, event publishing / handling, calls to other
services, persistence tables and configuration keys.

    python tools/context/conventions.py                # which presets each service uses, and what they find
    python tools/context/conventions.py --list         # every built-in preset and its detection marker

The language adapters (lang_python.py, lang_treesitter.py) only produce symbols. Everything framework-specific is
decided here, from rules over three things every language has:

  decorator        a symbol's own annotations / decorators / attributes (text without `@`, `#[`, `[`)
  class_decorator  the annotations of the class that owns a method (route prefixes, Feign clients, @Table)
  source / file    the source text (call-style routes such as Express / gin, `template.send("topic")`, env reads)

Presets are picked per service: `conventions:` in config/services.yaml (a list of names, or `auto`, the default),
where `auto` selects every preset whose `detect` marker occurs in the service's source. Teams with in-house
frameworks add their own presets in config/conventions.yaml (same schema as PRESETS below; see the scaffold for an
annotated example) and reference them by name, or give them a `detect` marker so `auto` finds them.

A rule that does not match finds nothing; nothing is inferred from naming alone. Facts found this way carry the
evidence `static` in the service graph, like the Python ones.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

HTTP = "(?P<method>get|post|put|patch|delete)"

PRESETS: dict[str, dict] = {
    # ---- Python
    "fastapi": {
        "detect": r"\bfrom fastapi\b|\bimport fastapi\b|\bAPIRouter\(", "languages": ["python"],
        "routes": [{"on": "decorator", "match": r"^(?:router|app|api|\w+_router)\." + HTTP + r"\(\s*['\"](?P<path>[^'\"]*)['\"]",
                    "prefix": {"on": "file", "match": r"APIRouter\([^)]*prefix\s*=\s*['\"](?P<prefix>[^'\"]+)['\"]"}}],
    },
    "flask": {
        "detect": r"\bfrom flask\b|\bimport flask\b", "languages": ["python"],
        "routes": [{"on": "decorator", "match": r"^\w+\.route\((?P<args>.*)\)$", "method": "GET",
                    "method_in_args": r"methods\s*=\s*[\[(]\s*['\"](?P<method>\w+)",
                    "prefix": {"on": "file", "match": r"Blueprint\([^)]*url_prefix\s*=\s*['\"](?P<prefix>[^'\"]+)"}},
                   {"on": "decorator", "match": r"^(?:bp|blueprint|app|\w+_bp)\." + HTTP + r"\((?P<args>.*)\)$",
                    "prefix": {"on": "file", "match": r"Blueprint\([^)]*url_prefix\s*=\s*['\"](?P<prefix>[^'\"]+)"}}],
    },
    # a lightweight Python service-kit convention (exact, AST-based): publish_event(topic=...), HANDLERS = {...} in
    # <package>/handlers.py, ServiceClient("<service>") in <package>/clients.py, gateway ROUTES in routes.py
    "python-servicekit": {
        "detect": r"\bpublish_event\(|^HANDLERS\s*=|\bServiceClient\(", "languages": ["python"],
        "native": ["publish_event", "handlers_dict", "service_client"],
    },
    # ---- JVM
    "spring": {
        "detect": r"\borg\.springframework\.(web|http|stereotype|cloud\.openfeign|boot)\b",
        "languages": ["java", "kotlin", "groovy"],
        "routes": [{"on": "decorator", "match": r"^(?P<method>Get|Post|Put|Patch|Delete)Mapping\b(?:\((?P<args>.*)\))?$",
                    "prefix": {"on": "class_decorator", "match": r"^RequestMapping\b(?:\((?P<args>.*)\))?$"}},
                   {"on": "decorator", "match": r"^RequestMapping\((?P<args>.*)\)$", "method": "GET",
                    "method_in_args": r"RequestMethod\.(?P<method>\w+)",
                    "prefix": {"on": "class_decorator", "match": r"^RequestMapping\b(?:\((?P<args>.*)\))?$"}}],
        "clients": [{"on": "class_decorator", "match": r"^FeignClient\((?P<args>.*)\)$",
                     "target_in_args": r"(?:name|value)\s*=\s*\"(?P<target>[^\"]+)\""},
                    {"on": "source", "match": r"\.(?P<verb>getForObject|getForEntity|postForObject|postForEntity|put|"
                                              r"delete|patchForObject|exchange)\(\s*\"(?P<url>[^\"]+)\""},
                    {"on": "source", "match": r"\." + HTTP + r"\(\)\s*\.uri\(\s*\"(?P<url>[^\"]+)\""}],
        "request_body": r"@RequestBody\s+(?:@[\w.]+(?:\([^)]*\))?\s+)*(?:final\s+)?(?P<type>[\w.]+)",
        "config_keys": [{"on": "source", "match": r"\$\{(?P<key>[\w.\-]+)(?::[^}]*)?\}"},
                        {"on": "source", "match": r"ConfigurationProperties\(\s*(?:prefix\s*=\s*|value\s*=\s*)?\"(?P<key>[^\"]+)\""}],
    },
    "spring-messaging": {
        "detect": r"\borg\.springframework\.(kafka|amqp|jms|cloud\.stream)\b|\bio\.awspring\b",
        "languages": ["java", "kotlin", "groovy"],
        "publishes": [{"on": "source", "match": r"\b\w*(?:[Tt]emplate|[Bb]ridge|[Pp]roducer|[Pp]ublisher)\s*\.\s*"
                                               r"(?:send|sendDefault|convertAndSend|publish)\(\s*"
                                               r"(?:\"(?P<topic>[^\"]+)\"|(?P<const>[A-Z][A-Z0-9_]*)\b)"}],
        "consumes": [{"on": "decorator", "match": r"^(?:KafkaListener|RabbitListener|JmsListener|SqsListener|StreamListener)"
                                                  r"\((?P<args>.*)\)$",
                      "topic_in_args": r"(?:topics|queues|destination|value)\s*=\s*\{?\s*\"(?P<topic>[^\"]+)\""}],
    },
    "jpa": {
        "detect": r"\b(?:javax|jakarta)\.persistence\b", "languages": ["java", "kotlin", "groovy"],
        "tables": [{"on": "class_decorator", "match": r"^Table\((?P<args>.*)\)$", "table_in_args": r"name\s*=\s*\"(?P<table>[^\"]+)\""},
                   {"on": "class_decorator", "match": r"^Entity\b(?:\((?P<args>.*)\))?$",
                    "table_in_args": r"name\s*=\s*\"(?P<table>[^\"]+)\"", "default": "class"}],
        "migrations": ["**/db/migration", "**/db/changelog", "**/liquibase", "**/flyway"],
    },
    "jaxrs": {
        "detect": r"\b(?:javax|jakarta)\.ws\.rs\b", "languages": ["java", "kotlin", "groovy"],
        "routes": [{"on": "decorator", "match": r"^(?P<method>GET|POST|PUT|PATCH|DELETE)$", "path_from": r"^Path\((?P<args>.*)\)$",
                    "prefix": {"on": "class_decorator", "match": r"^Path\((?P<args>.*)\)$"}}],
    },
    "micronaut": {
        "detect": r"\bio\.micronaut\.http\b", "languages": ["java", "kotlin", "groovy"],
        "routes": [{"on": "decorator", "match": r"^(?P<method>Get|Post|Put|Patch|Delete)\b(?:\((?P<args>.*)\))?$",
                    "prefix": {"on": "class_decorator", "match": r"^Controller\b(?:\((?P<args>.*)\))?$"}}],
    },
    # ---- .NET
    "aspnet": {
        "detect": r"\bMicrosoft\.AspNetCore\b|\[ApiController\]|\bControllerBase\b", "languages": ["csharp"],
        "routes": [{"on": "decorator", "match": r"^Http(?P<method>Get|Post|Put|Patch|Delete)\b(?:\((?P<args>.*)\))?$",
                    "path_from": r"^Route\((?P<args>.*)\)$",
                    "prefix": {"on": "class_decorator", "match": r"^Route\((?P<args>.*)\)$"}}],
        "request_body": r"\[FromBody\]\s*(?P<type>[\w.]+)",
        "clients": [{"on": "source", "match": r"\.(?P<method>Get|Post|Put|Patch|Delete)(?:FromJson|AsJson)?Async\(\s*\$?\"(?P<url>[^\"]+)\""}],
    },
    "efcore": {
        "detect": r"\bMicrosoft\.EntityFrameworkCore\b|\bDataAnnotations\.Schema\b", "languages": ["csharp"],
        "tables": [{"on": "class_decorator", "match": r"^Table\((?P<args>.*)\)$"}],
        "migrations": ["**/Migrations"],
    },
    # ---- Node
    "nestjs": {
        "detect": r"@nestjs/", "languages": ["typescript", "tsx", "javascript"],
        "routes": [{"on": "decorator", "match": r"^(?P<method>Get|Post|Put|Patch|Delete)\((?P<args>.*)\)$",
                    "prefix": {"on": "class_decorator", "match": r"^Controller\((?P<args>.*)\)$"}}],
        "request_body": r"@Body\([^)]*\)\s*\w+\s*:\s*(?P<type>[\w.]+)",
        "publishes": [{"on": "source", "match": r"\.\s*emit\(\s*['\"`](?P<topic>[^'\"`]+)"}],
        "consumes": [{"on": "decorator", "match": r"^(?:EventPattern|MessagePattern)\((?P<args>.*)\)$"}],
    },
    "express": {
        "detect": r"""require\(\s*['"]express['"]\s*\)|from\s+['"]express['"]|\bexpress\.Router\(""",
        "languages": ["typescript", "tsx", "javascript"],
        "routes": [{"on": "source", "match": r"\b(?:router|app|api|\w+Router)\." + HTTP +
                    r"""\(\s*['"`](?P<path>[^'"`]+)['"`]\s*,\s*(?:[\w.]+\s*,\s*)*(?P<handler>[\w.]+)\s*\)"""}],
    },
    "node-messaging": {
        "detect": r"""from\s+['"](?:kafkajs|amqplib|@aws-sdk/client-sns|@aws-sdk/client-sqs|@google-cloud/pubsub)['"]|"""
                  r"""require\(\s*['"](?:kafkajs|amqplib)['"]""",
        "languages": ["typescript", "tsx", "javascript"],
        "publishes": [{"on": "source", "match": r"\b\w*(?:producer|publisher|channel|topic)\w*\s*\.\s*(?:send|publish|sendToQueue)"
                                               r"\(\s*\{?\s*(?:topic\s*:\s*)?['\"`](?P<topic>[^'\"`]+)"}],
    },
    "typeorm": {
        "detect": r"""from\s+['"]typeorm['"]""", "languages": ["typescript", "tsx", "javascript"],
        "tables": [{"on": "class_decorator", "match": r"^Entity\b(?:\((?P<args>.*)\))?$", "default": "class"}],
        "migrations": ["**/migrations"],
    },
    # ---- Go
    "go-http": {
        "detect": r'"github\.com/(?:gin-gonic/gin|labstack/echo[^"]*|go-chi/chi[^"]*|gorilla/mux|gofiber/fiber[^"]*)"|"net/http"',
        "languages": ["go"],
        "routes": [{"on": "source", "match": r"\.(?P<method>GET|POST|PUT|PATCH|DELETE|Get|Post|Put|Patch|Delete)\(\s*\"(?P<path>/[^\"]*)\""
                                             r"\s*,\s*(?:[\w.]+\s*,\s*)*(?P<handler>[\w.]+)\s*\)"},
                   {"on": "source", "match": r"HandleFunc\(\s*\"(?P<path>/[^\"]*)\"\s*,\s*(?P<handler>[\w.]+)\s*\)"
                                             r"(?:\s*\.\s*Methods\(\s*\"(?P<method>\w+)\")?", "method": "ANY"}],
        "clients": [{"on": "source", "match": r"\bhttp\.(?P<method>Get|Post)\(\s*\"(?P<url>[^\"]+)\""}],
    },
    # ---- PHP
    "laravel": {
        "detect": r"\bIlluminate\\", "languages": ["php"],
        "routes": [{"on": "source", "match": r"Route::" + HTTP + r"""\(\s*['"](?P<path>[^'"]*)['"]\s*,\s*\[\s*(?P<class>\w+)::class\s*,\s*['"](?P<handler>\w+)['"]"""}],
    },
    "symfony": {
        "detect": r"\bSymfony\\Component\\Routing\b", "languages": ["php"],
        "routes": [{"on": "decorator", "match": r"^Route\((?P<args>.*)\)$", "method": "GET",
                    "method_in_args": r"methods\s*:\s*\[\s*['\"](?P<method>\w+)",
                    "prefix": {"on": "class_decorator", "match": r"^Route\((?P<args>.*)\)$"}}],
    },
}

# Environment-variable reads, any language: listed under config.env_vars in a manifest.
ENV_PATTERNS = [
    r"environ(?:\.get)?\(\s*['\"](\w+)",                 # Python os.environ[...] / os.environ.get(...)
    r"\bgetenv\(\s*['\"](\w+)",                          # Python os.getenv, C/PHP getenv
    r"System\.getenv\(\s*\"(\w+)\"",                     # Java / Kotlin
    r"process\.env\.(\w+)", r"process\.env\[\s*['\"](\w+)",   # Node
    r"os\.Getenv\(\s*\"(\w+)\"\)", r"os\.LookupEnv\(\s*\"(\w+)\"\)",   # Go
    r"GetEnvironmentVariable\(\s*\"(\w+)\"",             # .NET
    r"ENV\[\s*['\"](\w+)", r"ENV\.fetch\(\s*['\"](\w+)",  # Ruby
    r"std::env::var\(\s*\"(\w+)\"",                     # Rust
]
VERBS = {"getforobject": "GET", "getforentity": "GET", "postforobject": "POST", "postforentity": "POST",
         "put": "PUT", "delete": "DELETE", "patchforobject": "PATCH", "exchange": "ANY"}


# --------------------------------------------------------------------------- helpers


def _group(m: re.Match, name: str) -> str | None:
    """Named group `name`, or its single/back-quoted twin from STR (name_s / name_b)."""
    for key in (name, f"{name}_s", f"{name}_b"):
        if key in m.re.groupindex and m.group(key) is not None:
            return m.group(key)
    return None


def first_string(args: str | None, keys: tuple[str, ...] = ("path", "value", "name")) -> str | None:
    """The path / name argument of an annotation: `value = "/x"`, `path = {"/x"}`, or the first literal."""
    if not args:
        return None
    for key in keys:
        m = re.search(rf"\b{key}\s*[=:]\s*\{{?\s*[\"'`]([^\"'`]*)[\"'`]", args)
        if m:
            return m.group(1)
    m = re.search(r"[\"'`]([^\"'`]*)[\"'`]", args)
    return m.group(1) if m else None


def join_path(prefix: str, path: str) -> str:
    """Concatenate like the frameworks do: one slash between the parts, a leading slash, framework-specific
    parameter syntax (`:id`, `<int:id>`) normalised to the OpenAPI `{id}`."""
    if prefix and path:
        if prefix.endswith("/") and path.startswith("/"):
            joined = prefix + path[1:]
        elif not prefix.endswith("/") and not path.startswith("/"):
            joined = f"{prefix}/{path}"
        else:
            joined = prefix + path
    else:
        joined = prefix or path
    if joined and not joined.startswith("/") and not re.match(r"^\w+://", joined):
        joined = "/" + joined
    joined = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", joined)
    return re.sub(r"(?<=/):(\w+)", r"{\1}", joined)


def url_path_and_host(url: str) -> tuple[str, str | None]:
    """'http://billing:8003/invoices/{id}' -> ('/invoices/{id}', 'billing'); '/invoices' -> ('/invoices', None)."""
    m = re.match(r"^(?:\w+:)?//([^/:?#]+)(?::\d+)?(/[^?#]*)?", url)
    if m:
        return m.group(2) or "/", m.group(1)
    m = re.match(r"^\$\{([\w.\-]+)\}(/[^?#]*)?", url)       # "${inventory.url}/stock"
    if m:
        return m.group(2) or "/", m.group(1)
    return url.split("?")[0], None


# --------------------------------------------------------------------------- loading


def load_custom(root: Path) -> dict[str, dict]:
    path = root / "config" / "conventions.yaml"
    if not path.exists():
        return {}
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    presets = data.get("presets") or {}
    bad = [name for name, rules in presets.items() if not isinstance(rules, dict)]
    if bad:
        raise SystemExit(f"config/conventions.yaml: presets {bad} must be mappings")
    for preset in presets.values():
        for kind, value in preset.items():
            if isinstance(value, list):
                for rule in value:
                    # YAML 1.1 reads an unquoted `on:` key as the boolean true; it always means the rule target here
                    if isinstance(rule, dict) and True in rule:
                        rule["on"] = rule.pop(True)
                    if isinstance(rule, dict) and isinstance(rule.get("prefix"), dict) and True in rule["prefix"]:
                        rule["prefix"]["on"] = rule["prefix"].pop(True)
    return presets


def all_presets(root: Path) -> dict[str, dict]:
    return {**PRESETS, **load_custom(root)}


def select(declared, languages: set[str], texts: list[str], root: Path) -> list[str]:
    """Preset names for a service: the declared list (`auto` entries expand to every detected preset)."""
    presets = all_presets(root)
    declared = declared if isinstance(declared, list) else [declared or "auto"]
    out: list[str] = []
    for name in declared:
        if name == "auto":
            for pname, preset in presets.items():
                langs = set(preset.get("languages") or [])
                if langs and not langs & languages:
                    continue
                marker = preset.get("detect")
                if marker and any(re.search(marker, t, re.M) for t in texts) and pname not in out:
                    out.append(pname)
        elif name in presets:
            if name not in out:
                out.append(name)
        else:
            raise SystemExit(f"unknown convention preset `{name}` (built-in: {', '.join(PRESETS)}; "
                             "custom ones go in config/conventions.yaml)")
    return out


def rules(names: list[str], root: Path, kind: str) -> list[dict]:
    presets = all_presets(root)
    return [dict(r, preset=n) for n in names for r in presets[n].get(kind, [])]


def natives(names: list[str], root: Path) -> set[str]:
    presets = all_presets(root)
    return {x for n in names for x in presets[n].get("native", [])}


def migration_globs(names: list[str], root: Path) -> list[str]:
    presets = all_presets(root)
    return [g for n in names for g in presets[n].get("migrations", [])]


# --------------------------------------------------------------------------- rule evaluation


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _prefix(rule: dict, owner, file_text: str) -> str:
    spec = rule.get("prefix")
    if not spec:
        return ""
    if spec.get("on") == "file":
        m = re.search(spec["match"], file_text)
        return (_group(m, "prefix") or first_string(_group(m, "args")) or "") if m else ""
    if owner is None:
        return ""
    for deco in owner.decorators:
        m = re.search(spec["match"], deco)
        if m:
            return _group(m, "prefix") or first_string(_group(m, "args")) or ""
    return ""


def _tokens(path: str, sym, owner) -> str:
    if owner is not None:
        path = path.replace("[controller]", re.sub(r"Controller$", "", owner.name))
    return path.replace("[action]", sym.name)


def decorator_route(sym, owner, file_text: str, route_rules: list[dict]) -> tuple[str, str] | None:
    """(METHOD, path) from a symbol's own decorators."""
    for rule in route_rules:
        if rule.get("on") != "decorator":
            continue
        for deco in sym.decorators:
            m = re.search(rule["match"], deco)
            if not m:
                continue
            args = _group(m, "args")
            method = _group(m, "method")
            if not method and rule.get("method_in_args") and args:
                mm = re.search(rule["method_in_args"], args)
                method = mm.group("method") if mm else None
            path = _group(m, "path")
            if path is None:
                path = first_string(args) if args else None
            if path is None and rule.get("path_from"):
                for other in sym.decorators:
                    pm = re.search(rule["path_from"], other)
                    if pm:
                        path = _group(pm, "path") or first_string(_group(pm, "args")) or ""
                        break
            method = (method or rule.get("method") or "GET").upper()
            prefix = _prefix(rule, owner, file_text)
            return method, _tokens(join_path(prefix, path or ""), sym, owner)
    return None


def source_routes(file_text: str, route_rules: list[dict]) -> list[dict]:
    """Call-style routes (Express, gin, Laravel): [{method, path, handler, class, line}]."""
    out = []
    for rule in route_rules:
        if rule.get("on") != "source":
            continue
        for m in re.finditer(rule["match"], file_text):
            out.append({"method": (_group(m, "method") or rule.get("method") or "GET").upper(),
                        "path": join_path("", _group(m, "path") or ""), "handler": _group(m, "handler"),
                        "class": _group(m, "class"), "line": _line_of(file_text, m.start())})
    return out


def _resolve_const(file_text: str, const: str) -> str | None:
    m = re.search(rf"\b{re.escape(const)}\b[^=\n;]*=\s*[\"']([^\"']+)[\"']", file_text)
    return m.group(1) if m else None


def source_topics(file_text: str, publish_rules: list[dict]) -> list[tuple[str, int]]:
    out = []
    for rule in publish_rules:
        if rule.get("on", "source") != "source":
            continue
        for m in re.finditer(rule["match"], file_text):
            topic = _group(m, "topic") or (_resolve_const(file_text, m.group("const"))
                                           if "const" in m.re.groupindex and m.group("const") else None)
            if topic:
                out.append((topic, _line_of(file_text, m.start())))
    return out


def decorator_topics(sym, consume_rules: list[dict]) -> list[str]:
    topics = []
    for rule in consume_rules:
        if rule.get("on", "decorator") != "decorator":
            continue
        for deco in sym.decorators:
            m = re.search(rule["match"], deco)
            if not m:
                continue
            topic = _group(m, "topic")
            args = _group(m, "args")
            if not topic and args and rule.get("topic_in_args"):
                tm = re.search(rule["topic_in_args"], args)
                topic = tm.group("topic") if tm else None
            topic = topic or first_string(args, ("topics", "queues", "destination", "value", "topic"))
            if topic and topic not in topics:
                topics.append(topic)
    return topics


def class_table(sym, table_rules: list[dict]) -> str | None:
    for rule in table_rules:
        for deco in sym.decorators:
            m = re.search(rule["match"], deco)
            if not m:
                continue
            table = _group(m, "table")
            args = _group(m, "args")
            if not table and args and rule.get("table_in_args"):
                tm = re.search(rule["table_in_args"], args)
                table = tm.group("table") if tm else None
            if not table and args and not rule.get("table_in_args"):
                table = first_string(args, ("name", "value"))
            if table:
                return table
            if rule.get("default") == "class":
                return sym.name
    return None


def client_target(sym, client_rules: list[dict]) -> str | None:
    """Declarative clients (Feign, Retrofit-style): the class annotation names the target service."""
    for rule in client_rules:
        if rule.get("on") != "class_decorator":
            continue
        for deco in sym.decorators:
            m = re.search(rule["match"], deco)
            if not m:
                continue
            target = _group(m, "target")
            args = _group(m, "args")
            if not target and args and rule.get("target_in_args"):
                tm = re.search(rule["target_in_args"], args)
                target = tm.group("target") if tm else None
            return target or first_string(args, ("name", "value"))
    return None


def source_calls(file_text: str, client_rules: list[dict]) -> list[dict]:
    out = []
    for rule in client_rules:
        if rule.get("on") != "source":
            continue
        for m in re.finditer(rule["match"], file_text):
            verb = _group(m, "verb")
            method = (_group(m, "method") or VERBS.get((verb or "").lower()) or rule.get("method") or "GET").upper()
            url = _group(m, "url") or _group(m, "path") or ""
            path, host = url_path_and_host(url)
            out.append({"method": method, "path": path, "host": _group(m, "target") or host,
                        "line": _line_of(file_text, m.start())})
    return out


TYPE_WRAPPERS = {"ResponseEntity", "Mono", "Flux", "Optional", "List", "Set", "Collection", "Iterable", "Stream",
                 "CompletableFuture", "CompletionStage", "Future", "Task", "ValueTask", "ActionResult", "IActionResult",
                 "IEnumerable", "IList", "ICollection", "Promise", "Observable", "Page", "Slice", "Response", "Result",
                 "Uni", "Multi", "Array", "ReadonlyArray", "Vec", "Option", "list", "dict", "Sequence", "Iterator",
                 "HttpEntity", "Callable", "DeferredResult", "Either"}
NON_SCHEMA = {"void", "Void", "Unit", "String", "string", "str", "int", "long", "Long", "Integer", "bool", "boolean",
              "Boolean", "double", "Double", "float", "Float", "decimal", "number", "any", "object", "Object", "None",
              "Map", "HashMap", "Dictionary", "Record", "JsonNode", "byte", "Byte", "char", "Resource", "UUID",
              "Instant", "LocalDate", "LocalDateTime", "Date", "DateTime", "error", "interface", "T"}


def response_type(signature: str, name: str) -> str | None:
    """The DTO a route returns, from its signature: `public ResponseEntity<OrderDto> get(...)` / `get(...): Order` /
    `def get(...) -> Order`, wrappers (ResponseEntity, Mono, List, Task, Promise, ...) unwrapped."""
    typ = None
    m = re.search(r"\)\s*(?::|->)\s*([\w.<>\[\], ?|]+?)\s*$", signature)        # TS / Kotlin / Python / Rust / Swift
    if m:
        typ = m.group(1)
    else:
        m = re.search(r"([\w.<>\[\], ?]+?)\s+" + re.escape(name) + r"\s*[(<]", signature)   # Java / C# / Groovy
        typ = m.group(1) if m else None
    if not typ:
        return None
    names = [n.split(".")[-1] for n in re.findall(r"[A-Za-z_][\w.]*", typ)]
    names = [n for n in names if n not in TYPE_WRAPPERS and n not in NON_SCHEMA
             and n not in {"public", "private", "protected", "internal", "static", "final", "async", "override",
                           "virtual", "suspend", "open", "fun", "def", "func"}]
    return names[-1] if names else None


def request_type(source: str, names: list[str], root: Path) -> str | None:
    """The request-body DTO of a route (Spring @RequestBody, NestJS @Body(), ASP.NET [FromBody])."""
    presets = all_presets(root)
    for name in names:
        pattern = presets[name].get("request_body")
        if pattern:
            m = re.search(pattern, source)
            if m:
                return m.group("type").split(".")[-1]
    return None


def config_keys(text: str, key_rules: list[dict]) -> list[str]:
    keys = []
    for rule in key_rules:
        for m in re.finditer(rule["match"], text):
            key = _group(m, "key")
            if key and key not in keys:
                keys.append(key)
    return keys


def env_vars(text: str) -> list[str]:
    return sorted({v for p in ENV_PATTERNS for v in re.findall(p, text)})


# --------------------------------------------------------------------------- python natives (exact, AST)


def _path_template(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            else:
                parts.append("{" + ast.unparse(value.value) + "}")
        return "".join(parts)
    return None


def native_service_client_calls(path: Path) -> list[dict]:
    """ServiceClient usage in <package>/clients.py -> [{client, target, method, path, line}]."""
    if not path.exists():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = []
    methods = {"get", "post", "put", "patch", "delete"}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        targets: dict[str, str] = {}
        for node in ast.walk(cls):
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", None) == "ServiceClient" and node.value.args
                    and isinstance(node.value.args[0], ast.Constant)):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        targets[target.attr] = node.value.args[0].value
        for method in (n for n in cls.body if isinstance(n, ast.FunctionDef)):
            for node in ast.walk(method):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in methods and isinstance(node.func.value, ast.Attribute)
                        and node.func.value.attr in targets and node.args):
                    template = _path_template(node.args[0])
                    if template:
                        calls.append({"client": f"{cls.name}.{method.name}", "target": targets[node.func.value.attr],
                                      "method": node.func.attr.upper(), "path": template, "line": node.lineno})
    return calls


def native_publish_event(path: Path) -> list[tuple[str, int]]:
    """publish_event(..., topic="x") calls -> [(topic, line)]."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "publish_event":
            topic = next((k.value.value for k in node.keywords
                          if k.arg == "topic" and isinstance(k.value, ast.Constant)), None)
            if topic:
                found.append((topic, node.lineno))
    return found


def native_handlers_dict(path: Path) -> dict[str, str]:
    """topic -> handler function name, from a `HANDLERS = {...}` dict."""
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "HANDLERS" for t in node.targets):
            if isinstance(node.value, ast.Dict):
                return {k.value: v.id for k, v in zip(node.value.keys, node.value.values)
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Name)}
    return {}


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import common
    if "--list" in argv:
        for name, preset in all_presets(common.ROOT).items():
            kinds = [k for k in ("routes", "publishes", "consumes", "clients", "tables", "config_keys", "native") if preset.get(k)]
            print(f"{name:<18} {','.join(preset.get('languages') or ['any']):<28} {', '.join(kinds)}")
        return 0
    for service in common.code_targets():
        idx = common.symbol_index(service)
        routes = [(s.label(), *s.route) for s in idx.product_symbols() if s.route]
        print(f"== {service}: languages {sorted(idx.languages)}  presets {idx.conventions}")
        print(f"   routes {len(routes)}  handlers {common.handler_topics(service)}  tables {idx.tables}")
        for label, method, path in routes[:8]:
            print(f"     {method:<6} {path:<40} {label}")
        if service != "common":
            print(f"   publishes {[(p['topic'], p['symbol']) for p in common.publishers(service)]}")
            print(f"   calls {[(c['target'], c['method'], c['path']) for c in common.rest_calls(service)]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
