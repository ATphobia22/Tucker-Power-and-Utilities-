from __future__ import annotations

import copy
import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

import rfc8785


def _validate_finite(value: Any, path: str = "payload") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError(f"non-finite numeric value at {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _validate_finite(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_finite(child, f"{path}[{index}]")
        return
    raise ValueError(f"unsupported evidence value at {path}: {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class EvidenceNode:
    node_id: str
    provenance_id: str
    authority: str
    validation_status: str
    payload: dict[str, Any]
    parent_ids: tuple[str, ...] = ()
    timestamp_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z"))

    def __post_init__(self) -> None:
        if not self.node_id or not self.provenance_id or not self.authority:
            raise ValueError("evidence node identifiers and authority are required")
        _validate_finite(self.payload)

    def canonical_bytes(self) -> bytes:
        return rfc8785.dumps(
            {
                "authority": self.authority,
                "node_id": self.node_id,
                "parent_ids": list(self.parent_ids),
                "payload": self.payload,
                "provenance_id": self.provenance_id,
                "timestamp_utc": self.timestamp_utc,
                "validation_status": self.validation_status,
            }
        )

    @property
    def payload_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


class EvidenceLedger:
    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceNode] = {}

    def append(self, node: EvidenceNode) -> None:
        if node.node_id in self._nodes:
            raise ValueError(f"duplicate evidence node: {node.node_id}")
        for parent in node.parent_ids:
            if parent not in self._nodes:
                raise ValueError(f"unknown evidence parent: {parent}")
        self._nodes[node.node_id] = node

    def verify(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError(f"evidence DAG cycle detected at: {node_id}")
            if node_id in visited:
                return
            node = self._nodes[node_id]
            visiting.add(node_id)
            for parent in node.parent_ids:
                if parent not in self._nodes:
                    raise ValueError(f"broken evidence edge: {parent}")
                visit(parent)
            visiting.remove(node_id)
            visited.add(node_id)
            if node.payload_hash != hashlib.sha256(node.canonical_bytes()).hexdigest():
                raise ValueError(f"evidence hash mismatch: {node.node_id}")

        for node_id in self._nodes:
            visit(node_id)

    def get(self, node_id: str) -> EvidenceNode:
        return self._nodes[node_id]

    def snapshot(self) -> Mapping[str, EvidenceNode]:
        """Return a detached, read-only view of the current evidence graph."""
        return MappingProxyType(copy.deepcopy(self._nodes))
