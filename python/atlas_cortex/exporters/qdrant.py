"""
Atlas Cortex — Qdrant Exporter (Fase 13)

Converts Atlas Cortex MOC graph nodes into Qdrant-compatible points
with UUIDv5 derived from SHA-256 content hashes (Qdrant requires UUID, not hex).
"""

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger("atlas_cortex.exporters.qdrant")

# Namespace UUID for Atlas Cortex deterministic UUIDv5 generation
ATLAS_UUID_NAMESPACE = uuid.UUID("a1a5c0e7-3e00-4000-b000-000000000000")


def _sha256_to_uuid5(sha256_hex: str) -> str:
    """Convert a SHA-256 hex string to a deterministic UUIDv5."""
    return str(uuid.uuid5(ATLAS_UUID_NAMESPACE, sha256_hex))


def to_qdrant_points(
    moc_graph: dict,
    embeddings: Optional[dict[str, list[float]]] = None,
) -> list[dict]:
    """
    Convert Atlas Cortex MOC graph nodes into Qdrant point dicts.

    Each node becomes a Qdrant point with:
    - id: UUIDv5 derived from the node's SHA-256 content_hash
    - vector: embedding vector (if provided)
    - payload: all node metadata

    Args:
        moc_graph: Atlas Cortex MOC graph dictionary.
        embeddings: Optional mapping of node_id -> embedding vector.
                    If None, points are created without vectors (metadata-only).

    Returns:
        List of Qdrant-compatible point dictionaries.
    """
    points = []
    doc_id = moc_graph.get("doc_id", "unknown")

    # Pre-compute edge adjacency for payload enrichment
    edges_out: dict[str, list[str]] = {}
    edges_in: dict[str, list[str]] = {}
    for edge in moc_graph.get("edges", []):
        source = edge["source"]
        target = edge["target"]
        edge_type = edge.get("type", "unknown")

        if source not in edges_out:
            edges_out[source] = []
        edges_out[source].append(f"{edge_type}:{target}")

        if target not in edges_in:
            edges_in[target] = []
        edges_in[target].append(f"{edge_type}:{source}")

    for node in moc_graph.get("nodes", []):
        node_id = node["id"]
        content_hash = node.get("content_hash", node_id)
        point_id = _sha256_to_uuid5(content_hash)

        payload = {
            "atlas_node_id": node_id,
            "doc_id": doc_id,
            "type": node.get("type", "unknown"),
            "title": node.get("title", ""),
            "content": node.get("content", ""),
            "heading_path": node.get("heading_path", []),
            "content_hash": content_hash,
            "edges_out": edges_out.get(node_id, []),
            "edges_in": edges_in.get(node_id, []),
        }

        # Include table data if present
        if node.get("table"):
            payload["table_header"] = node["table"].get("header", [])
            payload["table_row_count"] = len(node["table"].get("rows", []))

        point: dict[str, Any] = {
            "id": point_id,
            "payload": payload,
        }

        if embeddings and node_id in embeddings:
            point["vector"] = embeddings[node_id]

        points.append(point)

    return points


def push_to_qdrant(
    moc_graph: dict,
    collection_name: str,
    url: str = "http://localhost:6333",
    embeddings: Optional[dict[str, list[float]]] = None,
    vector_size: int = 384,
    api_key: Optional[str] = None,
):
    """
    Push Atlas Cortex MOC graph directly to a Qdrant instance.

    Creates the collection if it doesn't exist.
    Uses upsert for idempotent operations.

    Requires: pip install atlas_cortex[qdrant]

    Args:
        moc_graph: Atlas Cortex MOC graph dictionary.
        collection_name: Qdrant collection name.
        url: Qdrant server URL.
        embeddings: Mapping of node_id -> embedding vector.
        vector_size: Dimension of embedding vectors (default: 384 for MiniLM).
        api_key: Optional API key for Qdrant Cloud.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance,
            PointStruct,
            VectorParams,
        )
    except ImportError:
        raise ImportError(
            "qdrant-client is required. Install it with: pip install atlas_cortex[qdrant]"
        )

    client = QdrantClient(url=url, api_key=api_key)

    # Create collection if it doesn't exist
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s", collection_name)

    # Build points
    raw_points = to_qdrant_points(moc_graph, embeddings=embeddings)

    points = []
    for rp in raw_points:
        vector = rp.get("vector", [0.0] * vector_size)
        points.append(
            PointStruct(
                id=rp["id"],
                vector=vector,
                payload=rp["payload"],
            )
        )

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch,
        )

    logger.info(
        "Upserted %d points to Qdrant collection '%s' at %s",
        len(points), collection_name, url,
    )
