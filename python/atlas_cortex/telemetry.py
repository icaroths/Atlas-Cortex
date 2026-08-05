"""
Atlas Cortex — Telemetry & Observability Module (Fase 10.5)

Lightweight structured logging for parse operations.
Activated via ATLAS_TELEMETRY=1 environment variable (off by default).
Emits JSON to stderr so it doesn't pollute stdout/pipeline output.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("atlas_cortex.telemetry")

# Global telemetry toggle
_TELEMETRY_ENABLED: Optional[bool] = None


def is_enabled() -> bool:
    """Check if telemetry is enabled via ATLAS_TELEMETRY env var."""
    global _TELEMETRY_ENABLED
    if _TELEMETRY_ENABLED is None:
        _TELEMETRY_ENABLED = os.environ.get("ATLAS_TELEMETRY", "0").strip() in ("1", "true", "yes")
    return _TELEMETRY_ENABLED


def enable():
    """Programmatically enable telemetry."""
    global _TELEMETRY_ENABLED
    _TELEMETRY_ENABLED = True


def disable():
    """Programmatically disable telemetry."""
    global _TELEMETRY_ENABLED
    _TELEMETRY_ENABLED = False


@dataclass
class ParseMetrics:
    """Structured metrics for a single parse operation."""

    event: str = "atlas_cortex.parse"
    doc_id: str = ""
    source_format: str = "markdown"
    input_bytes: int = 0
    parse_duration_ms: float = 0.0
    node_count: int = 0
    edge_count: int = 0
    node_types: dict[str, int] = field(default_factory=dict)
    edge_types: dict[str, int] = field(default_factory=dict)
    coverage_ratio: Optional[float] = None
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    timestamp_iso: str = ""
    parser_version: str = ""
    schema_version: str = ""

    def to_json(self) -> str:
        """Serialize to compact JSON string."""
        data = asdict(self)
        # Remove None fields for cleaner output
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, ensure_ascii=False)

    def emit(self):
        """Emit metrics as structured JSON to stderr."""
        if not is_enabled():
            return
        try:
            print(self.to_json(), file=sys.stderr, flush=True)
        except Exception as exc:
            logger.debug("Failed to emit telemetry metrics: %s", exc)


class ParseTimer:
    """Context manager that times a parse operation and emits metrics."""

    def __init__(self, doc_id: str = "", source_format: str = "markdown", input_bytes: int = 0):
        self.metrics = ParseMetrics(
            doc_id=doc_id,
            source_format=source_format,
            input_bytes=input_bytes,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
        )
        self._start_time = 0.0

    def __enter__(self) -> "ParseTimer":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter() - self._start_time) * 1000.0
        self.metrics.parse_duration_ms = round(elapsed, 2)
        if exc_type is not None:
            self.metrics.warnings.append(f"Parse failed: {exc_type.__name__}: {exc_val}")
        self.metrics.emit()
        return False  # Don't suppress exceptions

    def record_graph(self, graph: dict):
        """Extract metrics from a parsed MOC graph."""
        self.metrics.node_count = len(graph.get("nodes", []))
        self.metrics.edge_count = len(graph.get("edges", []))
        self.metrics.parser_version = graph.get("parser_version", "")
        self.metrics.schema_version = graph.get("schema_version", "")
        self.metrics.truncated = graph.get("truncated", False)

        # Count node types
        node_types: dict[str, int] = {}
        for node in graph.get("nodes", []):
            nt = node.get("type", "unknown")
            node_types[nt] = node_types.get(nt, 0) + 1
        self.metrics.node_types = node_types

        # Count edge types
        edge_types: dict[str, int] = {}
        for edge in graph.get("edges", []):
            et = edge.get("type", "unknown")
            edge_types[et] = edge_types.get(et, 0) + 1
        self.metrics.edge_types = edge_types
