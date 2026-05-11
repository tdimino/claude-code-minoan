"""Extract typed nodes from TypeScript repos.

Uses regex-based parsing (no ts-morph dependency) to extract:
- Exported function signatures with type annotations
- Zod schema definitions (z.object, z.string, etc.)
- Exported interfaces and type aliases
- Class method signatures
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base import BaseExtractor, RegistryNode


SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt",
    "coverage", ".turbo", ".cache",
}

TS_TYPE_MAP: dict[str, dict[str, Any]] = {
    "string": {"type": "string"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
    "null": {"type": "null"},
    "undefined": {"type": "null"},
    "void": {"type": "null"},
    "never": {},
    "any": {},
    "unknown": {},
    "object": {"type": "object"},
    "Date": {"type": "string", "format": "date-time"},
    "Uint8Array": {"type": "string", "contentEncoding": "base64"},
    "Buffer": {"type": "string", "contentEncoding": "base64"},
}

ZOD_TYPE_MAP: dict[str, dict[str, Any]] = {
    "z.string": {"type": "string"},
    "z.number": {"type": "number"},
    "z.boolean": {"type": "boolean"},
    "z.null": {"type": "null"},
    "z.undefined": {"type": "null"},
    "z.void": {"type": "null"},
    "z.any": {},
    "z.unknown": {},
    "z.date": {"type": "string", "format": "date-time"},
    "z.bigint": {"type": "integer"},
}

RE_EXPORT_FUNCTION = re.compile(
    r"export\s+(?:async\s+)?function\s+(\w+)"
    r"\s*(?:<[^>]*>)?"
    r"\s*\(([^)]*)\)"
    r"\s*(?::\s*([^{;]+))?"
    r"\s*[{;]",
    re.MULTILINE,
)

RE_EXPORT_CONST_ARROW = re.compile(
    r"export\s+const\s+(\w+)\s*"
    r"(?::\s*[^=]+)?"
    r"\s*=\s*(?:async\s+)?"
    r"\(([^)]*)\)"
    r"\s*(?::\s*([^=>{]+))?"
    r"\s*=>",
    re.MULTILINE,
)

RE_EXPORT_INTERFACE = re.compile(
    r"export\s+interface\s+(\w+)\s*(?:extends\s+[^{]+)?\s*\{([^}]*)\}",
    re.MULTILINE | re.DOTALL,
)

RE_EXPORT_TYPE = re.compile(
    r"export\s+type\s+(\w+)\s*(?:<[^>]*>)?\s*=\s*\{([^}]*)\}",
    re.MULTILINE | re.DOTALL,
)

RE_ZOD_SCHEMA = re.compile(
    r"export\s+const\s+(\w+)\s*=\s*z\.object\(\s*\{([^}]*)\}\s*\)",
    re.MULTILINE | re.DOTALL,
)

RE_INTERFACE_FIELD = re.compile(
    r"(\w+)\s*(\??)\s*:\s*(.+?)(?:;|$)",
    re.MULTILINE,
)

RE_PARAM = re.compile(
    r"(\w+)\s*(\??)\s*:\s*(.+?)(?:,|$)",
)


def _ts_type_to_schema(type_str: str) -> dict[str, Any]:
    """Convert a TypeScript type string to JSON Schema."""
    type_str = type_str.strip()

    if type_str in TS_TYPE_MAP:
        return TS_TYPE_MAP[type_str].copy()

    if type_str.endswith("[]"):
        inner = _ts_type_to_schema(type_str[:-2])
        return {"type": "array", "items": inner}

    if type_str.startswith("Array<") and type_str.endswith(">"):
        inner = _ts_type_to_schema(type_str[6:-1])
        return {"type": "array", "items": inner}

    if type_str.startswith("Promise<") and type_str.endswith(">"):
        return _ts_type_to_schema(type_str[8:-1])

    if type_str.startswith("Record<") and type_str.endswith(">"):
        inner = type_str[7:-1]
        parts = _split_type_args(inner)
        if len(parts) == 2:
            val_schema = _ts_type_to_schema(parts[1])
            return {"type": "object", "additionalProperties": val_schema}
        return {"type": "object"}

    if type_str.startswith("Map<") and type_str.endswith(">"):
        return {"type": "object"}

    if type_str.startswith("Set<") and type_str.endswith(">"):
        inner = _ts_type_to_schema(type_str[4:-1])
        return {"type": "array", "items": inner, "uniqueItems": True}

    if " | " in type_str:
        parts = [p.strip() for p in _split_union_types(type_str)]
        schemas = [_ts_type_to_schema(p) for p in parts]
        non_null = [s for s in schemas if s.get("type") != "null"]
        if len(non_null) == 1 and len(schemas) > 1:
            result = non_null[0].copy()
            result["nullable"] = True
            return result
        return {"anyOf": schemas}

    if type_str.startswith("'") or type_str.startswith('"'):
        val = type_str.strip("'\"")
        return {"const": val}

    return {"$ref": f"#/$defs/{type_str}"}


def _split_union_types(s: str) -> list[str]:
    parts = []
    depth = 0
    current = ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "<([{":
            depth += 1
            current += ch
        elif ch in ">)]}":
            depth -= 1
            current += ch
        elif depth == 0 and s[i:i+3] == " | ":
            parts.append(current.strip())
            current = ""
            i += 3
            continue
        else:
            current += ch
        i += 1
    if current.strip():
        parts.append(current.strip())
    return parts


def _split_type_args(s: str) -> list[str]:
    parts = []
    depth = 0
    current = ""
    for ch in s:
        if ch in "<([":
            depth += 1
            current += ch
        elif ch in ">)]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())
    return parts


def _parse_params(param_str: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for match in RE_PARAM.finditer(param_str):
        name, optional, type_str = match.group(1), match.group(2), match.group(3)
        properties[name] = _ts_type_to_schema(type_str.strip().rstrip(","))
        if not optional:
            required.append(name)
    result: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        result["required"] = required
    return result


def _parse_interface_body(body: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for match in RE_INTERFACE_FIELD.finditer(body):
        name, optional, type_str = match.group(1), match.group(2), match.group(3)
        properties[name] = _ts_type_to_schema(type_str.strip())
        if not optional:
            required.append(name)
    result: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        result["required"] = required
    return result


class TypeScriptExtractor(BaseExtractor):
    language = "typescript"

    def extract(self, root: Path) -> list[RegistryNode]:
        nodes: list[RegistryNode] = []
        ts_files = self._find_ts_files(root)

        for ts_file in ts_files:
            try:
                source = ts_file.read_text(errors="replace")
            except Exception:
                continue

            rel_path = str(ts_file.relative_to(root))
            module = rel_path.replace("/", ".").removesuffix(".ts").removesuffix(".tsx")

            nodes.extend(self._extract_functions(source, rel_path, module))
            nodes.extend(self._extract_interfaces(source, rel_path, module))
            nodes.extend(self._extract_type_aliases(source, rel_path, module))
            nodes.extend(self._extract_zod_schemas(source, rel_path, module))

        return nodes

    def _find_ts_files(self, root: Path) -> list[Path]:
        files = []
        for ext in ("*.ts", "*.tsx"):
            for p in root.rglob(ext):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                if p.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", ".d.ts")):
                    continue
                files.append(p)
        return sorted(files)

    def _extract_functions(self, source: str, file_path: str, module: str) -> list[RegistryNode]:
        nodes = []
        for pattern in (RE_EXPORT_FUNCTION, RE_EXPORT_CONST_ARROW):
            for match in pattern.finditer(source):
                name = match.group(1)
                params_str = match.group(2)
                return_type = match.group(3)

                input_schema = _parse_params(params_str) if params_str.strip() else {"type": "object", "properties": {}}
                output_schema = _ts_type_to_schema(return_type.strip()) if return_type else {}

                line = source[:match.start()].count("\n") + 1

                nodes.append(RegistryNode(
                    name=f"{module}.{name}",
                    kind="function",
                    language="typescript",
                    input_schema=input_schema,
                    output_schema=output_schema,
                    source_file=file_path,
                    source_line=line,
                    module=module,
                ))
        return nodes

    def _extract_interfaces(self, source: str, file_path: str, module: str) -> list[RegistryNode]:
        nodes = []
        for match in RE_EXPORT_INTERFACE.finditer(source):
            name = match.group(1)
            body = match.group(2)
            schema = _parse_interface_body(body)
            line = source[:match.start()].count("\n") + 1

            nodes.append(RegistryNode(
                name=f"{module}.{name}",
                kind="type_definition",
                language="typescript",
                input_schema=schema,
                output_schema=schema,
                source_file=file_path,
                source_line=line,
                module=module,
                tags=["interface"],
            ))
        return nodes

    def _extract_type_aliases(self, source: str, file_path: str, module: str) -> list[RegistryNode]:
        nodes = []
        for match in RE_EXPORT_TYPE.finditer(source):
            name = match.group(1)
            body = match.group(2)
            schema = _parse_interface_body(body)
            line = source[:match.start()].count("\n") + 1

            nodes.append(RegistryNode(
                name=f"{module}.{name}",
                kind="type_definition",
                language="typescript",
                input_schema=schema,
                output_schema=schema,
                source_file=file_path,
                source_line=line,
                module=module,
                tags=["type_alias"],
            ))
        return nodes

    def _extract_zod_schemas(self, source: str, file_path: str, module: str) -> list[RegistryNode]:
        nodes = []
        for match in RE_ZOD_SCHEMA.finditer(source):
            name = match.group(1)
            body = match.group(2)
            schema = self._zod_body_to_schema(body)
            line = source[:match.start()].count("\n") + 1

            nodes.append(RegistryNode(
                name=f"{module}.{name}",
                kind="class",
                language="typescript",
                input_schema=schema,
                output_schema=schema,
                source_file=file_path,
                source_line=line,
                module=module,
                tags=["zod"],
            ))
        return nodes

    def _zod_body_to_schema(self, body: str) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []

        optional_re = re.compile(r"(\w+)\s*:\s*z\.(\w+)\(\)\.optional\(\)", re.MULTILINE)
        optional_fields: set[str] = set()
        for match in optional_re.finditer(body):
            fname = match.group(1)
            ztype = f"z.{match.group(2)}"
            properties[fname] = ZOD_TYPE_MAP.get(ztype, {}).copy()
            optional_fields.add(fname)

        field_re = re.compile(r"(\w+)\s*:\s*z\.(\w+)\(\)", re.MULTILINE)
        for match in field_re.finditer(body):
            fname = match.group(1)
            if fname in optional_fields:
                continue
            ztype = f"z.{match.group(2)}"
            properties[fname] = ZOD_TYPE_MAP.get(ztype, {}).copy()
            required.append(fname)

        result: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            result["required"] = required
        return result
