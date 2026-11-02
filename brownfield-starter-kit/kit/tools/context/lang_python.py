"""Symbol extraction for Python with the standard library `ast` (exact, no grammar package needed).

Yields the same facts as tools/context/lang_treesitter.py for every other language: module-level functions,
classes and their methods, with line ranges (decorators included), referenced identifiers, string constants,
decorators, signature, docstring, bases and annotated class attributes. SQLAlchemy-style `__tablename__` is read
here too because it is plain Python, not a framework convention.
"""
from __future__ import annotations

import ast


def _collect(node: ast.AST) -> tuple[set[str], set[str]]:
    refs, strings = set(), set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            refs.add(child.id)
        elif isinstance(child, ast.Attribute):
            refs.add(child.attr)
        elif isinstance(child, ast.keyword) and child.arg:
            refs.add(child.arg)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str) and len(child.value) < 80:
            strings.add(child.value)
    return refs, strings


def _entry(node: ast.AST, qualname: str, kind: str) -> dict:
    refs, strings = _collect(node)
    decorators = [ast.unparse(d) for d in getattr(node, "decorator_list", [])]
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    bases, fields = [], {}
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(b) for b in node.bases]
        signature = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields[item.target.id] = ast.unparse(item.annotation)
    else:
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        signature = f"{prefix} {node.name}({ast.unparse(node.args)}){returns}"
    return {"qualname": qualname, "kind": kind, "start": start, "end": node.end_lineno or node.lineno,
            "refs": refs - {qualname.rsplit(".", 1)[-1]}, "strings": strings, "decorators": decorators,
            "signature": signature, "docstring": ast.get_docstring(node) or "", "bases": bases, "fields": fields}


def extract(text: str, language: str = "python") -> dict:
    """Returns {"symbols", "module_doc", "class_fields", "tables"}; empty on a syntax error (never a guess)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"symbols": [], "module_doc": "", "class_fields": {}, "tables": {}, "error": "syntax error"}
    symbols, class_fields, tables = [], {}, {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(_entry(node, node.name, "function"))
        elif isinstance(node, ast.ClassDef):
            symbols.append(_entry(node, node.name, "class"))
            fields = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(_entry(item, f"{node.name}.{item.name}", "method"))
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(item.value, ast.Constant):
                                tables[node.name] = item.value.value
            class_fields[node.name] = fields
    return {"symbols": symbols, "module_doc": ast.get_docstring(tree) or "", "class_fields": class_fields,
            "tables": tables}
