"""Tests for the Atlas Cortex Exporters (Fase 13)."""

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "python"))

from atlas_cortex.exporters.neo4j import to_cypher, to_cypher_params
from atlas_cortex.exporters.qdrant import _sha256_to_uuid5, to_qdrant_points


# Fixture: a realistic MOC graph
@pytest.fixture
def sample_moc_graph():
    return {
        "schema_version": "1.0.0",
        "parser_version": "2.0-enterprise",
        "doc_id": "test-doc-001",
        "truncated": False,
        "nodes": [
            {
                "id": "abc123_1",
                "type": "heading",
                "title": "Introduction",
                "content": "# Introduction",
                "raw_content": "# Introduction",
                "heading_path": ["Introduction"],
                "content_hash": "aaa111",
            },
            {
                "id": "abc123_2",
                "type": "paragraph",
                "title": "Introduction",
                "content": "This is a test paragraph with [link](#conclusion).",
                "raw_content": "This is a test paragraph with [link](#conclusion).",
                "heading_path": ["Introduction"],
                "content_hash": "bbb222",
            },
            {
                "id": "abc123_3",
                "type": "table",
                "title": "Data Table",
                "content": "| A | B |\n|---|---|\n| 1 | 2 |",
                "raw_content": "| A | B |\n|---|---|\n| 1 | 2 |",
                "heading_path": ["Introduction", "Data Table"],
                "content_hash": "ccc333",
                "table": {"header": ["A", "B"], "rows": [["1", "2"]]},
            },
        ],
        "edges": [
            {
                "id": "edge_001",
                "source": "abc123_2",
                "target": "abc123_1",
                "type": "child_of",
                "method": "heading_hierarchy",
            },
            {
                "id": "edge_002",
                "source": "abc123_2",
                "target": "abc123_3",
                "type": "references",
                "method": "anchor_link",
            },
            {
                "id": "edge_003",
                "source": "abc123_1",
                "target": "abc123_3",
                "type": "semantically_related",
                "method": "knn_semantic",
            },
        ],
    }


class TestNeo4jExporter:
    def test_to_cypher_generates_valid_script(self, sample_moc_graph):
        cypher = to_cypher(sample_moc_graph)
        assert "MERGE (n:AtlasNode {id: node.id})" in cypher
        assert "CREATE CONSTRAINT" in cypher
        assert "doc_id: test-doc-001" in cypher

    def test_to_cypher_includes_all_edge_types(self, sample_moc_graph):
        cypher = to_cypher(sample_moc_graph)
        assert "CHILD_OF" in cypher
        assert "REFERENCES" in cypher
        assert "SEMANTICALLY_RELATED" in cypher

    def test_to_cypher_params_structure(self, sample_moc_graph):
        params = to_cypher_params(sample_moc_graph)
        assert params["doc_id"] == "test-doc-001"
        assert len(params["nodes"]) == 3
        assert "child_of_edges" in params
        assert "references_edges" in params
        assert len(params["child_of_edges"]) == 1
        assert len(params["references_edges"]) == 1

    def test_to_cypher_empty_graph(self):
        empty = {"doc_id": "empty", "nodes": [], "edges": []}
        cypher = to_cypher(empty)
        assert "doc_id: empty" in cypher
        # Should still have constraint but no UNWIND for nodes/edges
        assert "CREATE CONSTRAINT" in cypher

    def test_to_cypher_idempotent(self, sample_moc_graph):
        c1 = to_cypher(sample_moc_graph)
        c2 = to_cypher(sample_moc_graph)
        assert c1 == c2


class TestQdrantExporter:
    def test_sha256_to_uuid5_deterministic(self):
        u1 = _sha256_to_uuid5("abc123")
        u2 = _sha256_to_uuid5("abc123")
        assert u1 == u2
        # Validate UUID format
        parsed = uuid.UUID(u1)
        assert parsed.version == 5

    def test_sha256_to_uuid5_different_inputs(self):
        u1 = _sha256_to_uuid5("abc123")
        u2 = _sha256_to_uuid5("def456")
        assert u1 != u2

    def test_to_qdrant_points_basic(self, sample_moc_graph):
        points = to_qdrant_points(sample_moc_graph)
        assert len(points) == 3

        # Each point has id, payload
        for point in points:
            assert "id" in point
            assert "payload" in point
            # UUID format
            uuid.UUID(point["id"])
            assert point["payload"]["doc_id"] == "test-doc-001"

    def test_to_qdrant_points_with_embeddings(self, sample_moc_graph):
        embeddings = {
            "abc123_1": [0.1] * 384,
            "abc123_2": [0.2] * 384,
            "abc123_3": [0.3] * 384,
        }
        points = to_qdrant_points(sample_moc_graph, embeddings=embeddings)
        for point in points:
            assert "vector" in point
            assert len(point["vector"]) == 384

    def test_to_qdrant_points_without_embeddings(self, sample_moc_graph):
        points = to_qdrant_points(sample_moc_graph)
        for point in points:
            assert "vector" not in point

    def test_to_qdrant_points_preserves_edge_adjacency(self, sample_moc_graph):
        points = to_qdrant_points(sample_moc_graph)
        # Node abc123_2 has 2 outgoing edges
        node2_point = [p for p in points if p["payload"]["atlas_node_id"] == "abc123_2"][0]
        assert len(node2_point["payload"]["edges_out"]) == 2

    def test_to_qdrant_points_includes_table_metadata(self, sample_moc_graph):
        points = to_qdrant_points(sample_moc_graph)
        table_point = [p for p in points if p["payload"]["type"] == "table"][0]
        assert table_point["payload"]["table_header"] == ["A", "B"]
        assert table_point["payload"]["table_row_count"] == 1
