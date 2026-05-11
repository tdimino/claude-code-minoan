"""Extract typed nodes from Python repos.

Handles: Pydantic BaseModel, dataclasses, TypedDict, and plain
function annotations. Converts to JSON Schema for the registry.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from .base import BaseExtractor, RegistryNode


BUILTIN_TYPE_MAP: dict[str, dict[str, Any]] = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "None": {"type": "null"},
    "NoneType": {"type": "null"},
    "bytes": {"type": "string", "contentEncoding": "base64"},
    "Any": {},
    "dict": {"type": "object"},
    "list": {"type": "array"},
    "tuple": {"type": "array"},
    "set": {"type": "array", "uniqueItems": True},
    "frozenset": {"type": "array", "uniqueItems": True},
    "datetime": {"type": "string", "format": "date-time"},
    "date": {"type": "string", "format": "date"},
    "Path": {"type": "string"},
    "UUID": {"type": "string", "format": "uuid"},
    "Decimal": {"type": "string", "pattern": "^-?\\d+(\\.\\d+)?$"},
}

SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env", "node_modules",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
}


def _annotation_to_schema(node: ast.expr | None) -> dict[str, Any]:
    """Convert a Python type annotation AST node to JSON Schema."""
    if node is None:
        return {}

    if isinstance(node, ast.Constant):
        if node.value is None:
            return {"type": "null"}
        return {}

    if isinstance(node, ast.Name):
        name = node.id
        if name in BUILTIN_TYPE_MAP:
            return BUILTIN_TYPE_MAP[name].copy()
        return {"$ref": f"#/$defs/{name}"}

    if isinstance(node, ast.Attribute):
        attr = _resolve_attribute(node)
        if attr in BUILTIN_TYPE_MAP:
            return BUILTIN_TYPE_MAP[attr].copy()
        return {"$ref": f"#/$defs/{attr}"}

    if isinstance(node, ast.Subscript):
        return _subscript_to_schema(node)

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _annotation_to_schema(node.left)
        right = _annotation_to_schema(node.right)
        schemas = []
        for s in (left, right):
            if "anyOf" in s:
                schemas.extend(s["anyOf"])
            else:
                schemas.append(s)
        if len(schemas) == 2 and {"type": "null"} in schemas:
            non_null = [s for s in schemas if s != {"type": "null"}]
            if non_null:
                result = non_null[0].copy()
                result["nullable"] = True
                return result
        return {"anyOf": schemas}

    return {}


def _resolve_attribute(node: ast.Attribute) -> str:
    parts = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _subscript_to_schema(node: ast.Subscript) -> dict[str, Any]:
    origin = ""
    if isinstance(node.value, ast.Name):
        origin = node.value.id
    elif isinstance(node.value, ast.Attribute):
        origin = _resolve_attribute(node.value)

    slice_node = node.slice

    if origin in ("list", "List"):
        items = _annotation_to_schema(slice_node)
        return {"type": "array", "items": items}

    if origin in ("set", "Set", "frozenset", "FrozenSet"):
        items = _annotation_to_schema(slice_node)
        return {"type": "array", "items": items, "uniqueItems": True}

    if origin in ("dict", "Dict"):
        if isinstance(slice_node, ast.Tuple) and len(slice_node.elts) == 2:
            val_schema = _annotation_to_schema(slice_node.elts[1])
            return {"type": "object", "additionalProperties": val_schema}
        return {"type": "object"}

    if origin in ("tuple", "Tuple"):
        if isinstance(slice_node, ast.Tuple):
            return {
                "type": "array",
                "prefixItems": [_annotation_to_schema(e) for e in slice_node.elts],
                "minItems": len(slice_node.elts),
                "maxItems": len(slice_node.elts),
            }
        return {"type": "array"}

    if origin in ("Optional",):
        inner = _annotation_to_schema(slice_node)
        return inner

    if origin in ("Union",):
        if isinstance(slice_node, ast.Tuple):
            schemas = [_annotation_to_schema(e) for e in slice_node.elts]
            non_null = [s for s in schemas if s != {"type": "null"}]
            if len(non_null) == 1:
                return non_null[0]
            return {"anyOf": schemas}
        return _annotation_to_schema(slice_node)

    if origin in ("Literal",):
        if isinstance(slice_node, ast.Tuple):
            values = [e.value for e in slice_node.elts if isinstance(e, ast.Constant)]
            return {"enum": values}
        if isinstance(slice_node, ast.Constant):
            return {"const": slice_node.value}
        return {}

    if origin in ("Annotated",):
        if isinstance(slice_node, ast.Tuple) and slice_node.elts:
            return _annotation_to_schema(slice_node.elts[0])
        return {}

    if origin in ("Sequence", "Iterable", "Iterator", "Generator"):
        items = _annotation_to_schema(slice_node)
        return {"type": "array", "items": items}

    return {"$ref": f"#/$defs/{origin}"}


def _get_docstring(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            val = node.body[0].value.value
            if isinstance(val, str):
                first_line = val.strip().split("\n")[0]
                return first_line
    return ""


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _infer_tags(name: str, docstring: str) -> list[str]:
    tags = []
    combined = (name + " " + docstring).lower()
    tag_keywords = {
        "validate": "validate",
        "transform": "transform",
        "parse": "transform",
        "convert": "transform",
        "fetch": "io",
        "read": "io",
        "write": "io",
        "load": "io",
        "save": "io",
        "send": "io",
        "upload": "io",
        "download": "io",
        "auth": "auth",
        "login": "auth",
        "token": "auth",
        "filter": "filter",
        "sort": "filter",
        "search": "filter",
        "create": "crud",
        "update": "crud",
        "delete": "crud",
        "get": "crud",
    }
    for keyword, tag in tag_keywords.items():
        if keyword in combined and tag not in tags:
            tags.append(tag)
    return tags


def _has_side_effects(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                if child.func.attr in ("write", "send", "post", "put", "delete", "execute", "commit"):
                    return True
            if isinstance(child.func, ast.Name):
                if child.func.id in ("print", "open"):
                    return True
    return False


class PythonExtractor(BaseExtractor):
    language = "python"

    def extract(self, root: Path) -> list[RegistryNode]:
        nodes: list[RegistryNode] = []
        py_files = self._find_python_files(root)

        for py_file in py_files:
            try:
                source = py_file.read_text(errors="replace")
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            rel_path = str(py_file.relative_to(root))
            module = rel_path.replace("/", ".").removesuffix(".py")
            if module.endswith(".__init__"):
                module = module.removesuffix(".__init__")

            exports = self._get_exports(tree)

            for item in ast.iter_child_nodes(tree):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not _is_public(item.name):
                        continue
                    if exports is not None and item.name not in exports:
                        continue
                    node = self._extract_function(item, rel_path, module)
                    if node:
                        nodes.append(node)

                elif isinstance(item, ast.ClassDef):
                    if not _is_public(item.name):
                        continue
                    if exports is not None and item.name not in exports:
                        continue
                    class_nodes = self._extract_class(item, rel_path, module, source)
                    nodes.extend(class_nodes)

        return nodes

    def _find_python_files(self, root: Path) -> list[Path]:
        files = []
        for p in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.name.startswith("test_") or p.name.endswith("_test.py"):
                continue
            files.append(p)
        return sorted(files)

    def _get_exports(self, tree: ast.Module) -> set[str] | None:
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            return {
                                elt.value
                                for elt in node.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            }
        return None

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        module: str,
    ) -> RegistryNode | None:
        args = node.args
        has_annotations = node.returns is not None or any(
            a.annotation is not None for a in args.args
        )
        if not has_annotations:
            return None

        input_schema = self._args_to_schema(args)
        output_schema = _annotation_to_schema(node.returns)
        docstring = _get_docstring(node)
        tags = _infer_tags(node.name, docstring)
        side_effects = _has_side_effects(node)

        return RegistryNode(
            name=f"{module}.{node.name}",
            kind="function",
            language="python",
            input_schema=input_schema,
            output_schema=output_schema,
            source_file=file_path,
            source_line=node.lineno,
            end_line=node.end_lineno,
            description=docstring,
            module=module,
            tags=tags,
            side_effects=side_effects,
        )

    def _args_to_schema(self, args: ast.arguments) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        all_args = args.args[:]
        if all_args and all_args[0].arg in ("self", "cls"):
            all_args = all_args[1:]

        defaults_offset = len(all_args) - len(args.defaults)

        for i, arg in enumerate(all_args):
            if arg.annotation is None:
                continue
            schema = _annotation_to_schema(arg.annotation)
            properties[arg.arg] = schema
            if i < defaults_offset:
                required.append(arg.arg)

        result: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result

    def _extract_class(
        self,
        node: ast.ClassDef,
        file_path: str,
        module: str,
        source: str,
    ) -> list[RegistryNode]:
        nodes: list[RegistryNode] = []
        is_pydantic = self._is_pydantic_model(node)
        is_dataclass = self._is_dataclass(node)
        is_typed_dict = self._is_typed_dict(node)
        docstring = _get_docstring(node)

        if is_pydantic or is_dataclass or is_typed_dict:
            schema = self._class_fields_to_schema(node)
            kind_label = "pydantic" if is_pydantic else "dataclass" if is_dataclass else "typeddict"
            nodes.append(RegistryNode(
                name=f"{module}.{node.name}",
                kind="class",
                language="python",
                input_schema=schema,
                output_schema=schema,
                source_file=file_path,
                source_line=node.lineno,
                end_line=node.end_lineno,
                description=docstring,
                module=module,
                tags=[kind_label],
            ))

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not _is_public(item.name) or item.name == "__init__":
                    continue
                fn_node = self._extract_function(item, file_path, f"{module}.{node.name}")
                if fn_node:
                    fn_node.kind = "method"
                    nodes.append(fn_node)

        return nodes

    def _is_pydantic_model(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            name = ""
            if isinstance(base, ast.Name):
                name = base.id
            elif isinstance(base, ast.Attribute):
                name = base.attr
            if name in ("BaseModel", "BaseSettings"):
                return True
        return False

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        for dec in node.decorator_list:
            name = ""
            if isinstance(dec, ast.Name):
                name = dec.id
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                name = dec.func.id
            elif isinstance(dec, ast.Attribute):
                name = dec.attr
            if name == "dataclass":
                return True
        return False

    def _is_typed_dict(self, node: ast.ClassDef) -> bool:
        for base in node.bases:
            name = ""
            if isinstance(base, ast.Name):
                name = base.id
            elif isinstance(base, ast.Attribute):
                name = base.attr
            if name == "TypedDict":
                return True
        return False

    def _class_fields_to_schema(self, node: ast.ClassDef) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                if field_name.startswith("_"):
                    continue
                schema = _annotation_to_schema(item.annotation)
                properties[field_name] = schema
                if item.value is None:
                    required.append(field_name)

        result: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result
