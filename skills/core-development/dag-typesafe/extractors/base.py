"""Abstract base for language-specific type extractors."""

from __future__ import annotations

import json
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RegistryNode:
    name: str
    kind: str
    language: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    source_file: str
    source_line: int
    description: str = ""
    param_schema: dict[str, Any] | None = None
    module: str = ""
    end_line: int | None = None
    tags: list[str] = field(default_factory=list)
    side_effects: bool = False
    idempotent: bool = False
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "kind": self.kind,
            "language": self.language,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "source_ref": {
                "file": self.source_file,
                "line": self.source_line,
            },
        }
        if self.description:
            d["description"] = self.description
        if self.param_schema:
            d["param_schema"] = self.param_schema
        if self.module:
            d["source_ref"]["module"] = self.module
        if self.end_line:
            d["source_ref"]["end_line"] = self.end_line
        if self.tags:
            d["tags"] = self.tags
        if self.side_effects:
            d["side_effects"] = True
        if self.idempotent:
            d["idempotent"] = True
        if self.dependencies:
            d["dependencies"] = self.dependencies
        return d


class BaseExtractor(ABC):
    language: str = ""

    @abstractmethod
    def extract(self, root: Path) -> list[RegistryNode]:
        """Walk the repo from `root` and return typed nodes for public API surface."""

    def build_registry(self, root: Path) -> dict[str, Any]:
        nodes = self.extract(root)
        source_content = ""
        for node in nodes:
            src = root / node.source_file
            if src.exists():
                source_content += src.read_text(errors="replace")

        return {
            "version": "1.0.0",
            "metadata": {
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "source_root": str(root.resolve()),
                "languages": [self.language],
                "extractor_versions": {self.language: "1.0.0"},
                "node_count": len(nodes),
                "source_hash": hashlib.sha256(source_content.encode()).hexdigest(),
            },
            "nodes": [n.to_dict() for n in nodes],
        }

    def write_registry(self, root: Path, output: Path | None = None) -> Path:
        registry = self.build_registry(root)
        out = output or (root / "dag-registry.json")
        out.write_text(json.dumps(registry, indent=2))
        return out
