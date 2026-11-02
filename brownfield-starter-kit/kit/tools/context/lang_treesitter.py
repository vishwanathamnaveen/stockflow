"""Symbol extraction for non-Python languages with tree-sitter (the grammars graphify already installs).

    python tools/context/lang_treesitter.py <file> [<file> ...]    # print the symbols a file yields (debugging)

One generic walker plus a small table per language. It yields the same facts the Python adapter
(tools/context/lang_python.py) yields, so the manifest, the enrichment and the service graph never look at syntax:

  qualname   Outer.Inner.method (Go receivers, Rust impl blocks and C++ `A::f` become the type's methods)
  kind       class | function | method
  start/end  1-based lines; start includes leading annotations / decorators / attributes
  refs       identifiers used in the body; accessor calls also count as the property they read or write
             (getShipDate / setShipDate / isActive -> shipDate / active), so Lombok, JavaBeans and C#/Kotlin
             properties trace like plain fields
  strings    string literals (< 80 chars): topics, paths, keys, flags
  decorators annotation / decorator / attribute text without the leading `@`, `#[` or `[`
  signature  declaration text up to the body, whitespace collapsed, annotations removed
  docstring  the doc comment directly above the declaration (Javadoc, KDoc, `///`, `#`, `//`)
  bases      super types (extends / implements / base lists / delegation specifiers)
  fields     class fields, properties, record / data-class / case-class components and enum constants

Unknown constructs are skipped, never guessed: a file this module cannot parse yields no symbols (the manifest then
reports what it could not resolve instead of inventing it).
"""
from __future__ import annotations

import importlib
import re
import sys
from functools import lru_cache
from pathlib import Path

# extension -> language key. Only languages whose grammar imports are used; others are reported, not indexed.
EXTENSIONS = {
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".cs": "csharp", ".ts": "typescript", ".tsx": "tsx",
    ".mts": "typescript", ".cts": "typescript", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".go": "go", ".rb": "ruby", ".php": "php", ".rs": "rust", ".scala": "scala",
    ".swift": "swift", ".groovy": "groovy", ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp",
    ".hpp": "cpp", ".hh": "cpp",
}
GRAMMARS = {   # language -> (module, function)
    "java": ("tree_sitter_java", "language"), "kotlin": ("tree_sitter_kotlin", "language"),
    "csharp": ("tree_sitter_c_sharp", "language"), "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"), "javascript": ("tree_sitter_javascript", "language"),
    "go": ("tree_sitter_go", "language"), "ruby": ("tree_sitter_ruby", "language"),
    "php": ("tree_sitter_php", "language_php"), "rust": ("tree_sitter_rust", "language"),
    "scala": ("tree_sitter_scala", "language"), "swift": ("tree_sitter_swift", "language"),
    "groovy": ("tree_sitter_groovy", "language"), "c": ("tree_sitter_c", "language"),
    "cpp": ("tree_sitter_cpp", "language"),
}

_TS_CLASS = {"class_declaration", "abstract_class_declaration", "interface_declaration", "enum_declaration"}
_TS_FUNC = {"function_declaration", "method_definition", "generator_function_declaration", "method_signature",
            "abstract_method_signature"}
_TS_FIELDS = {"public_field_definition", "property_signature", "field_definition"}
SPECS: dict[str, dict] = {
    "java": {"class": {"class_declaration", "interface_declaration", "enum_declaration", "record_declaration",
                       "annotation_type_declaration"},
             "function": {"method_declaration", "constructor_declaration", "compact_constructor_declaration"},
             "fields": {"field_declaration", "constant_declaration"}, "enum_members": {"enum_constant"},
             "record_params": {"record_declaration"}},
    "groovy": {"class": {"class_declaration", "interface_declaration", "enum_declaration"},
               "function": {"method_declaration", "constructor_declaration", "function_definition"},
               "fields": {"field_declaration"}, "enum_members": {"enum_constant"}},
    "kotlin": {"class": {"class_declaration", "object_declaration", "companion_object", "interface_declaration"},
               "function": {"function_declaration", "secondary_constructor"},
               "fields": {"property_declaration"}, "enum_members": {"enum_entry"},
               "record_params": {"class_declaration"}},
    "csharp": {"class": {"class_declaration", "interface_declaration", "struct_declaration", "record_declaration",
                         "record_struct_declaration", "enum_declaration"},
               "function": {"method_declaration", "constructor_declaration", "local_function_statement",
                            "operator_declaration"},
               "fields": {"field_declaration", "property_declaration", "event_field_declaration"},
               "enum_members": {"enum_member_declaration"}, "record_params": {"record_declaration",
                                                                             "record_struct_declaration"}},
    "typescript": {"class": _TS_CLASS, "function": _TS_FUNC, "fields": _TS_FIELDS, "enum_members": {"enum_assignment"},
                   "arrow": True},
    "tsx": {"class": _TS_CLASS, "function": _TS_FUNC, "fields": _TS_FIELDS, "enum_members": {"enum_assignment"},
            "arrow": True},
    "javascript": {"class": {"class_declaration"}, "function": {"function_declaration", "method_definition",
                                                                "generator_function_declaration"},
                   "fields": {"field_definition"}, "arrow": True},
    "go": {"class": {"type_spec"}, "function": {"function_declaration", "method_declaration"},
           "fields": {"field_declaration"}, "wrappers": {"type_declaration"}},
    "ruby": {"class": {"class", "module", "singleton_class"}, "function": {"method", "singleton_method"},
             "fields": set()},
    "php": {"class": {"class_declaration", "interface_declaration", "trait_declaration", "enum_declaration"},
            "function": {"method_declaration", "function_definition"}, "fields": {"property_declaration"},
            "enum_members": {"enum_case"}},
    "rust": {"class": {"struct_item", "enum_item", "trait_item", "union_item", "impl_item", "mod_item"},
             "function": {"function_item", "function_signature_item"}, "fields": {"field_declaration"},
             "enum_members": {"enum_variant"}},
    "scala": {"class": {"class_definition", "object_definition", "trait_definition", "enum_definition"},
              "function": {"function_definition", "function_declaration"},
              "fields": {"val_definition", "var_definition"}, "record_params": {"class_definition"}},
    "swift": {"class": {"class_declaration", "protocol_declaration"},
              "function": {"function_declaration", "init_declaration", "protocol_function_declaration"},
              "fields": {"property_declaration"}, "enum_members": {"enum_entry"}},
    "c": {"class": {"struct_specifier"}, "function": {"function_definition"}, "fields": {"field_declaration"}},
    "cpp": {"class": {"class_specifier", "struct_specifier"}, "function": {"function_definition"},
            "fields": {"field_declaration"}},
}

WRAPPERS = {"export_statement", "decorated_definition", "ambient_declaration", "export_declaration", "template_declaration"}
DECORATOR_TYPES = {"annotation", "marker_annotation", "decorator", "attribute", "attribute_item", "attribute_group"}
MODIFIER_CONTAINERS = {"modifiers", "modifier", "attribute_list", "attribute_lists", "decorators"}
NAME_TYPES = {"identifier", "type_identifier", "simple_identifier", "constant", "name", "property_identifier",
              "field_identifier", "constructor", "operator_name", "destructor_name"}
BODY_TYPES = {"class_body", "declaration_list", "block", "body", "statement_block", "function_body", "enum_body",
              "interface_body", "field_declaration_list", "compound_statement", "template_body", "body_statement",
              "enum_class_body", "protocol_body", "enum_variant_list", "constructor_body", "record_declaration_body",
              "annotation_type_body", "object_literal"}
BASE_CONTAINERS = {"superclass", "super_interfaces", "extends_interfaces", "base_list", "class_heritage", "extends_clause",
                   "implements_clause", "delegation_specifiers", "base_class_clause", "base_clause",
                   "class_interface_clause", "inheritance_specifier", "type_inheritance_clause", "extends_type_clause",
                   "trait_bounds"}
TYPE_REF_TYPES = {"type_identifier", "identifier", "user_type", "constant", "name", "scoped_type_identifier",
                  "generic_type", "qualified_name", "simple_identifier", "scope_resolution"}
STRING_CONTENT = {"string_fragment", "string_content", "string_literal_content", "interpreted_string_literal_content",
                  "raw_string_literal_content", "multi_line_string_content", "line_string_content",
                  "string_value", "escape_sequence"}
ACCESSOR = re.compile(r"^(get|set|is|has)([A-Z][A-Za-z0-9_]*)$")
ANNOTATION_TEXT = re.compile(r"@[\w.]+(\((?:[^()]|\([^()]*\))*\))?|#\[[^\]]*\]")
PARAM_ATTRIBUTE = re.compile(r"\[\s*[A-Z]\w*(\((?:[^()]|\([^()]*\))*\))?\s*\]\s*")


class Unsupported(RuntimeError):
    pass


@lru_cache
def parser(language: str):
    try:
        from tree_sitter import Language, Parser
        module, fn = GRAMMARS[language]
        return Parser(Language(getattr(importlib.import_module(module), fn)()))
    except (ImportError, AttributeError, KeyError) as exc:
        raise Unsupported(f"no tree-sitter grammar for {language} ({exc}); pip install -r requirements.txt") from exc


def language_of(path: Path | str) -> str | None:
    return EXTENSIONS.get(Path(path).suffix.lower())


def _text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _named(node):
    return [c for c in node.children if c.is_named]


def _decapitalize(name: str) -> str:
    return name[:1].lower() + name[1:] if not (len(name) > 1 and name[:2].isupper()) else name


def _string_value(node, src: bytes) -> str:
    parts = [c for c in node.children if c.type in STRING_CONTENT]
    if parts:
        return "".join(_text(p, src) for p in parts)
    text = _text(node, src)
    text = re.sub(r"^[@$a-zA-Z]{0,2}(?=[\"'`])", "", text)
    for q in ('"""', "'''", '"', "'", "`"):
        if len(text) >= 2 * len(q) and text.startswith(q) and text.endswith(q):
            return text[len(q):-len(q)]
    return text


def _collect(node, src: bytes, skip_name: str) -> tuple[set[str], set[str]]:
    refs, strings = set(), set()
    stack = [node]
    while stack:
        n = stack.pop()
        t = n.type
        if "string" in t and "content" not in t and "fragment" not in t and t not in STRING_CONTENT:
            value = _string_value(n, src)
            if len(value) < 80:
                strings.add(value)
            # interpolations inside templates may still reference identifiers
            stack.extend(c for c in n.children if c.type not in STRING_CONTENT and c.is_named)
            continue
        if t in NAME_TYPES or t.endswith("identifier"):
            name = _text(n, src).lstrip("$@")
            if name and re.match(r"^[A-Za-z_]\w*$", name):
                refs.add(name)
                m = ACCESSOR.match(name)
                if m:
                    refs.add(_decapitalize(m.group(2)))
        stack.extend(n.children)
    refs.discard(skip_name)
    return refs, strings


def _name_of(node, src: bytes, language: str) -> str | None:
    if node.type == "impl_item":                      # Rust: impl Type / impl Trait for Type -> Type
        typ = node.child_by_field_name("type")
        return re.sub(r"<.*", "", _text(typ, src)) if typ else None
    if node.type == "function_definition" and language in ("c", "cpp"):
        decl = node.child_by_field_name("declarator")
        while decl is not None and decl.type not in ("function_declarator",):
            decl = decl.child_by_field_name("declarator")
        target = decl.child_by_field_name("declarator") if decl is not None else None
        return _text(target, src).split("::")[-1] if target is not None else None
    name = node.child_by_field_name("name")
    if name is not None:
        return _text(name, src).lstrip("$")
    for child in _named(node):
        if child.type in NAME_TYPES:
            return _text(child, src).lstrip("$")
        if child.type in ("user_type", "type_identifier"):
            return _text(child, src)
    return None


def _cpp_owner(node, src: bytes) -> str | None:
    """`int Order::price()` defined outside its class -> Order."""
    decl = node.child_by_field_name("declarator")
    while decl is not None and decl.type != "function_declarator":
        decl = decl.child_by_field_name("declarator")
    target = decl.child_by_field_name("declarator") if decl is not None else None
    if target is not None and "::" in _text(target, src):
        return _text(target, src).rsplit("::", 1)[0].split("::")[-1]
    return None


def _go_receiver(node, src: bytes) -> str | None:
    recv = node.child_by_field_name("receiver")
    if recv is None:
        return None
    found = re.findall(r"[A-Za-z_]\w*", _text(recv, src))
    return found[-1] if found else None


def _anchor(node):
    """The node whose siblings hold the doc comment / decorators: a wrapper (export, decorated) when present."""
    while node.parent is not None and node.parent.type in WRAPPERS | {"type_declaration"}:
        node = node.parent
    return node


def _decorators(node, src: bytes) -> list:
    found = []
    for child in node.children:
        if child.type in DECORATOR_TYPES:
            found.append(child)
        elif child.type in MODIFIER_CONTAINERS:
            found += [c for c in child.children if c.type in DECORATOR_TYPES] or (
                [child] if child.type == "attribute_list" else [])
    anchor = _anchor(node)
    for holder in {anchor, node}:
        sib = holder.prev_named_sibling
        while sib is not None and (sib.type in DECORATOR_TYPES or sib.type in ("attribute_list",)):
            found.insert(0, sib)
            sib = sib.prev_named_sibling
        if holder is not node:
            found = [c for c in holder.children if c.type in DECORATOR_TYPES] + found
    seen, out = set(), []
    for d in found:
        if d.id not in seen:
            seen.add(d.id)
            out.append(d)
    return out


def _decorator_text(node, src: bytes) -> list[str]:
    text = _text(node, src).strip()
    if node.type == "attribute_list" or (text.startswith("[") and text.endswith("]")):
        inner = text[1:-1].strip()
        return [p.strip() for p in re.split(r",\s*(?![^()]*\))", inner) if p.strip()]
    if text.startswith("#[") and text.endswith("]"):
        return [text[2:-1].strip()]
    return [text.lstrip("@").strip()]


def _doc(node, src: bytes) -> str:
    sib = _anchor(node).prev_sibling
    while sib is not None and sib.type in DECORATOR_TYPES | {"attribute_list"}:
        sib = sib.prev_sibling
    lines = []
    while sib is not None and "comment" in sib.type:
        if lines and sib.end_point[0] < lines[0][0] - 1:
            break
        lines.insert(0, (sib.start_point[0], _text(sib, src)))
        sib = sib.prev_sibling
    if not lines:
        return ""
    text = "\n".join(t for _, t in lines)
    text = re.sub(r"^\s*/\*\*?|\*/\s*$", "", text, flags=re.M)
    text = re.sub(r"(?m)^\s*(///?|\*|#)\s?", "", text)
    text = re.sub(r"</?(summary|remarks|returns|param[^>]*)>", "", text)
    return text.strip()


def _signature(node, src: bytes) -> str:
    body = node.child_by_field_name("body")
    if node.type == "variable_declarator" and node.child_by_field_name("value") is not None:
        body = node.child_by_field_name("value").child_by_field_name("body")     # const f = (...) => {...}
    if body is None:
        body = next((c for c in node.children if c.type in BODY_TYPES), None)
    end = body.start_byte if body is not None else node.end_byte
    # the declaration starts after its own leading annotations / attributes (they are kept in `decorators`)
    start = node.start_byte
    for d in _decorators(node, src):
        if d.parent is not None and d.parent.type in ("attribute_list", "attribute_group"):
            d = d.parent.parent if d.parent.parent is not None and d.parent.parent.type == "attribute_list" else d.parent
        if node.start_byte <= d.start_byte and d.end_byte <= end:
            start = max(start, d.end_byte)
    text = src[start:end].decode("utf-8", errors="replace")
    text = ANNOTATION_TEXT.sub(" ", text)                     # parameter annotations: @Valid, @RequestBody, #[..]
    text = PARAM_ATTRIBUTE.sub("", text)                      # C# parameter attributes: [FromBody]
    text = re.sub(r"\s+", " ", text).strip().rstrip("{=;:").strip()
    text = re.sub(r"([(<\[])\s+", r"\1", text)
    return text[:300]


def _bases(node, src: bytes) -> list[str]:
    out = []

    def visit(n, top) -> None:
        if n.type in TYPE_REF_TYPES and n is not top:
            text = re.sub(r"<.*|\(.*", "", _text(n, src)).strip()
            if text and text not in out:
                out.append(text)
            return
        for c in _named(n):
            visit(c, top)

    for child in node.children:
        if child.type in BASE_CONTAINERS:
            visit(child, child)
    return out


def _decl_names(node, src: bytes) -> list[tuple[str, str]]:
    """Field names (+ type text) declared by one field/property node."""
    typ = node.child_by_field_name("type")
    type_text = _text(typ, src) if typ is not None else ""
    names = []
    for child in node.children:
        if typ is not None and child.start_byte == typ.start_byte and child.end_byte == typ.end_byte:
            continue                                   # the declared type, not a name (C# `IRepo _repo`)
        if child.type in ("variable_declarator", "property_element", "variable_declaration", "property_identifier",
                          "field_identifier", "identifier", "simple_identifier", "pattern", "name"):
            if child.type == "variable_declaration" and any(c.type == "variable_declarator" for c in child.children):
                if not type_text and child.child_by_field_name("type") is not None:
                    type_text = _text(child.child_by_field_name("type"), src)
                names += [n for n, _ in _decl_names(child, src)]
                continue
            if child.type in ("variable_declarator", "variable_declaration", "property_element"):
                name = child.child_by_field_name("name") or next((c for c in _named(child) if c.type in NAME_TYPES
                                                                  or c.type in ("variable_name", "pattern")), None)
                if name is not None and name.type == "variable_name":
                    name = next((c for c in _named(name) if c.type == "name"), name)
                if name is not None:
                    names.append(_text(name, src).lstrip("$"))
                    if not type_text:
                        t = child.child_by_field_name("type") or next(
                            (c for c in _named(child) if c.type in ("user_type", "type_annotation")), None)
                        type_text = _text(t, src).lstrip(": ").strip() if t is not None else ""
            elif node.type not in ("property_declaration",) or child.type != "name":
                names.append(_text(child, src).lstrip("$"))
        elif child.type == "type_annotation" and not type_text:
            type_text = _text(child, src).lstrip(": ").strip()
    if not names:
        name = node.child_by_field_name("name")
        if name is not None:
            names.append(_text(name, src).lstrip("$"))
    return [(n, type_text) for n in dict.fromkeys(names) if re.match(r"^[A-Za-z_]\w*$", n)]


def _record_params(node, src: bytes, language: str) -> list[tuple[str, str]]:
    out = []
    for child in node.children:
        if child.type in ("formal_parameters", "parameter_list", "primary_constructor", "class_parameters"):
            stack = [child]
            while stack:
                n = stack.pop(0)
                if n.type in ("formal_parameter", "parameter", "class_parameter", "record_component"):
                    if language == "kotlin" and not re.match(r"^\s*(\w+\s+)*(val|var)\b", _text(n, src)) \
                            and "data" not in _text(node, src).split("class")[0]:
                        continue
                    name = n.child_by_field_name("name") or next((c for c in _named(n) if c.type in NAME_TYPES), None)
                    typ = n.child_by_field_name("type") or next(
                        (c for c in _named(n) if c.type in ("user_type", "type_identifier", "predefined_type",
                                                            "generic_type")), None)
                    if name is not None:
                        out.append((_text(name, src), _text(typ, src) if typ is not None else ""))
                else:
                    stack.extend(_named(n))
    return out


def _class_fields(node, src: bytes, language: str, spec: dict) -> dict[str, str]:
    fields: dict[str, str] = {}
    if node.type in spec.get("record_params", set()):
        fields.update(_record_params(node, src, language))
    body = node.child_by_field_name("body") or next((c for c in node.children if c.type in BODY_TYPES), None)
    if node.type == "type_spec":           # Go: type X struct {...}
        typ = node.child_by_field_name("type")
        body = next((c for c in _named(typ) if c.type == "field_declaration_list"), None) if typ is not None else None
    if body is None:
        return fields
    stack = list(body.children)
    while stack:
        child = stack.pop(0)
        if child.type in spec.get("fields", set()):
            fields.update({n: t for n, t in _decl_names(child, src)})
        elif child.type in spec.get("enum_members", set()):
            name = child.child_by_field_name("name") or next((c for c in _named(child) if c.type in NAME_TYPES), None)
            if name is not None:
                fields[_text(name, src)] = "enum constant"
        elif child.type in ("enum_body_declarations", "enum_class_body", "enum_variant_list", "enum_member_declaration_list"):
            stack = list(child.children) + stack
        elif child.type == "method_definition" and _name_of(child, src, language) == "constructor":
            for param in (c for c in _named(child.child_by_field_name("parameters") or child) if c.type == "required_parameter"):
                if any(c.type == "accessibility_modifier" for c in param.children):   # TS parameter properties
                    pattern = param.child_by_field_name("pattern")
                    if pattern is not None:
                        fields[_text(pattern, src)] = ""
    return fields


def _arrow_name(node, src: bytes) -> str | None:
    """`const handler = async (...) => {}` / `export const f = function () {}`."""
    if node.type != "variable_declarator":
        return None
    value = node.child_by_field_name("value")
    if value is not None and value.type in ("arrow_function", "function_expression", "function"):
        name = node.child_by_field_name("name")
        return _text(name, src) if name is not None else None
    return None


def extract(text: str, language: str) -> dict:
    """Parse one file. Returns {"symbols": [dict], "module_doc": str, "class_fields": {class: [field]}}."""
    spec = SPECS[language]
    src = text.encode("utf-8")
    tree = parser(language).parse(src)
    symbols: list[dict] = []
    class_fields: dict[str, list[str]] = {}

    def add(node, qualname: str, kind: str, extra_fields: dict | None = None) -> None:
        decos = _decorators(node, src)
        start = min([node.start_point[0]] + [d.start_point[0] for d in decos]) + 1
        refs, strings = _collect(node, src, qualname.rsplit(".", 1)[-1])
        entry = {"qualname": qualname, "kind": kind, "start": start, "end": node.end_point[0] + 1,
                 "refs": refs, "strings": strings,
                 "decorators": [t for d in decos for t in _decorator_text(d, src)],
                 "signature": _signature(node, src), "docstring": _doc(node, src),
                 "bases": _bases(node, src) if kind == "class" else [], "fields": extra_fields or {}}
        symbols.append(entry)

    def walk(node, owners: list[str]) -> None:
        for child in node.children:
            t = child.type
            if t in spec["class"]:
                name = _name_of(child, src, language)
                if not name:
                    walk(child, owners)
                    continue
                if t == "type_spec":
                    typ = child.child_by_field_name("type")
                    if typ is None or typ.type not in ("struct_type", "interface_type"):
                        continue
                if t == "impl_item":                        # Rust impl: methods belong to the type, no new symbol
                    walk(child, owners + [name])
                    continue
                qual = ".".join(owners + [name])
                fields = _class_fields(child, src, language, spec)
                existing = next((s for s in symbols if s["qualname"] == qual and s["kind"] == "class"), None)
                if existing is None:
                    add(child, qual, "class", fields)
                class_fields.setdefault(name, [])
                class_fields[name] += [f for f in fields if f not in class_fields[name]]
                walk(child, owners + [name])
            elif t in spec["function"]:
                name = _name_of(child, src, language)
                if not name:
                    continue
                owner = owners
                if language == "go" and t == "method_declaration":
                    recv = _go_receiver(child, src)
                    owner = owners + [recv] if recv else owners
                elif language == "cpp" and not owners:
                    cls = _cpp_owner(child, src)
                    owner = [cls] if cls else owners
                qual = ".".join(owner + [name])
                add(child, qual, "method" if owner else "function")
            elif spec.get("arrow") and t == "variable_declarator" and _arrow_name(child, src):
                qual = ".".join(owners + [_arrow_name(child, src)])
                add(child, qual, "method" if owners else "function")
            else:
                walk(child, owners)

    walk(tree.root_node, [])
    module_doc = ""     # a header comment above everything else (license banners are kept: they are rare and short)
    for child in tree.root_node.children:
        if child.type == "php_tag":
            continue
        if "comment" in child.type and child.next_named_sibling is not None                 and "comment" not in child.next_named_sibling.type                 and child.next_named_sibling.type in ("package_declaration", "package_clause", "import_declaration",
                                                      "using_directive", "namespace_declaration", "import_statement",
                                                      "file_scoped_namespace_declaration", "import_list", "header"):
            module_doc = _doc_text(_text(child, src))
        break
    return {"symbols": symbols, "module_doc": module_doc, "class_fields": class_fields}


def _doc_text(text: str) -> str:
    text = re.sub(r"^\s*/\*\*?|\*/\s*$", "", text, flags=re.M)
    return re.sub(r"(?m)^\s*(///?|\*|#)\s?", "", text).strip()


def main(argv: list[str]) -> int:
    for path in argv:
        language = language_of(path)
        if language is None:
            print(f"{path}: no adapter for {Path(path).suffix}")
            continue
        out = extract(Path(path).read_text(encoding="utf-8", errors="replace"), language)
        print(f"== {path} ({language})  module doc: {out['module_doc'][:60]!r}")
        for s in out["symbols"]:
            print(f"  {s['kind']:<8} {s['qualname']:<40} L{s['start']}-{s['end']}  deco={s['decorators']}  "
                  f"bases={s['bases']} fields={list(s['fields'])[:6]}")
            print(f"           sig: {s['signature'][:110]}")
            if s["docstring"]:
                print(f"           doc: {s['docstring'][:80]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
