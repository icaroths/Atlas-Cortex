"""Tests for the Atlas Cortex Telemetry Module (Fase 10.5)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "python"))

from atlas_cortex.telemetry import (
    ParseMetrics,
    ParseTimer,
    enable,
    disable,
    is_enabled,
)


class TestParseMetrics:
    def test_to_json_basic(self):
        m = ParseMetrics(doc_id="test-doc", node_count=5, edge_count=3)
        j = m.to_json()
        data = json.loads(j)
        assert data["doc_id"] == "test-doc"
        assert data["node_count"] == 5
        assert data["edge_count"] == 3

    def test_to_json_omits_none(self):
        m = ParseMetrics(doc_id="test", coverage_ratio=None)
        j = m.to_json()
        data = json.loads(j)
        assert "coverage_ratio" not in data

    def test_to_json_includes_value(self):
        m = ParseMetrics(doc_id="test", coverage_ratio=0.95)
        j = m.to_json()
        data = json.loads(j)
        assert data["coverage_ratio"] == 0.95


class TestParseTimer:
    def test_timer_records_duration(self):
        with ParseTimer(doc_id="timer-test") as timer:
            _ = sum(range(1000))
        assert timer.metrics.parse_duration_ms > 0

    def test_timer_records_graph(self):
        graph = {
            "nodes": [
                {"id": "1", "type": "heading", "content": "Title"},
                {"id": "2", "type": "paragraph", "content": "Text"},
            ],
            "edges": [
                {"id": "e1", "type": "child_of", "source": "2", "target": "1"},
            ],
            "parser_version": "2.0",
            "schema_version": "1.0.0",
            "truncated": False,
        }
        with ParseTimer(doc_id="graph-test") as timer:
            timer.record_graph(graph)

        assert timer.metrics.node_count == 2
        assert timer.metrics.edge_count == 1
        assert timer.metrics.node_types == {"heading": 1, "paragraph": 1}
        assert timer.metrics.edge_types == {"child_of": 1}
        assert timer.metrics.parser_version == "2.0"

    def test_timer_handles_exception(self):
        with pytest.raises(ValueError):
            with ParseTimer(doc_id="error-test") as timer:
                raise ValueError("test error")

        assert len(timer.metrics.warnings) == 1
        assert "ValueError" in timer.metrics.warnings[0]


class TestTelemetryToggle:
    def test_enable_disable(self):
        enable()
        assert is_enabled()
        disable()
        assert not is_enabled()

    def test_emit_when_disabled(self, capsys):
        disable()
        m = ParseMetrics(doc_id="silent")
        m.emit()
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_emit_when_enabled(self, capsys):
        enable()
        m = ParseMetrics(doc_id="loud", node_count=10)
        m.emit()
        disable()
        captured = capsys.readouterr()
        assert "loud" in captured.err
        assert "node_count" in captured.err
