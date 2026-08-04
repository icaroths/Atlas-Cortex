"""
Atlas Cortex — Neo4j Exporter (Fase 13)

Converts Atlas Cortex MOC graphs to Neo4j Cypher statements for idempotent
ingestion, or pushes directly to a Neo4j instance via the official driver.
"""

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger("atlas_cortex.exporters.neo4j")


def to_cypher(moc_graph: dict, batch_size: int = 500) -> str:
    """
    Generate idempotent Cypher MERGE statements from an Atlas Cortex MOC graph.

    Uses MERGE (not CREATE) so re-running the same graph is safe and idempotent.
    Properties are updated via ON CREATE SET / ON MATCH SET.

    Args:
        moc_graph: Atlas Cortex MOC graph dictionary.
        batch_size: Number of operations per UNWIND batch.

    Returns:
        Complete Cypher script as a string.
    """
    lines = []
    doc_id = moc_graph.get("doc_id", "unknown")
    schema_version = moc_graph.get("schema_version", "1.0.0")
    parser_version = moc_graph.get("parser_version", "2.0")

    lines.append(f"// Atlas Cortex Neo4j Import — doc_id: {doc_id}")
    lines.append(f"// Schema: {schema_version} | Parser: {parser_version}")
    lines.append(f"// Generated nodes: {len(moc_graph.get('nodes', []))} | edges: {len(moc_graph.get('edges', []))}")
    lines.append("")

    # Create constraint for idempotency
    lines.append("CREATE CONSTRAINT atlas_node_id IF NOT EXISTS FOR (n:AtlasNode) REQUIRE n.id IS UNIQUE;")
    lines.append("")

    # Nodes
    nodes = moc_graph.get("nodes", [])
    if nodes:
        lines.append("// --- Nodes ---")
        lines.append("UNWIND $nodes AS node")
        lines.append("MERGE (n:AtlasNode {id: node.id})")
        lines.append("ON CREATE SET")
        lines.append("  n.type = node.type,")
        lines.append("  n.title = node.title,")
        lines.append("  n.content = node.content,")
        lines.append("  n.raw_content = node.raw_content,")
        lines.append("  n.content_hash = node.content_hash,")
        lines.append("  n.heading_path = node.heading_path,")
        lines.append("  n.doc_id = $doc_id")
        lines.append("ON MATCH SET")
        lines.append("  n.content = node.content,")
        lines.append("  n.raw_content = node.raw_content,")
        lines.append("  n.content_hash = node.content_hash,")
        lines.append("  n.heading_path = node.heading_path;")
        lines.append("")

    # Edges
    edges = moc_graph.get("edges", [])
    if edges:
        # Group edges by type for cleaner Cypher
        edge_types = {}
        for edge in edges:
            et = edge.get("type", "RELATED_TO").upper().replace(" ", "_")
            if et not in edge_types:
                edge_types[et] = []
            edge_types[et].append(edge)

        for edge_type, typed_edges in edge_types.items():
            lines.append(f"// --- Edges: {edge_type} ---")
            lines.append(f"UNWIND ${edge_type.lower()}_edges AS edge")
            lines.append("MATCH (src:AtlasNode {id: edge.source})")
            lines.append("MATCH (tgt:AtlasNode {id: edge.target})")
            lines.append(f"MERGE (src)-[r:{edge_type} {{id: edge.id}}]->(tgt)")
            lines.append("ON CREATE SET r.method = edge.method;")
            lines.append("")

    return "\n".join(lines)


def to_cypher_params(moc_graph: dict) -> dict:
    """
    Generate the parameter dictionary to accompany the Cypher script.

    Returns:
        Dictionary with $nodes, $doc_id, and edge arrays keyed by type.
    """
    params = {
        "doc_id": moc_graph.get("doc_id", "unknown"),
        "nodes": moc_graph.get("nodes", []),
    }

    edges = moc_graph.get("edges", [])
    edge_types: dict[str, list] = {}
    for edge in edges:
        et = edge.get("type", "RELATED_TO").upper().replace(" ", "_")
        key = f"{et.lower()}_edges"
        if key not in edge_types:
            edge_types[key] = []
        edge_types[key].append(edge)

    params.update(edge_types)
    return params


def push_to_neo4j(
    moc_graph: dict,
    uri: str,
    auth: tuple[str, str],
    database: str = "neo4j",
):
    """
    Push an Atlas Cortex MOC graph directly to a Neo4j instance.

    Requires the `neo4j` Python driver: pip install atlas_cortex[neo4j]

    Args:
        moc_graph: Atlas Cortex MOC graph dictionary.
        uri: Neo4j connection URI (e.g., "bolt://localhost:7687").
        auth: Tuple of (username, password).
        database: Target database name.
    """
    try:
        from neo4j import GraphDatabase
    except ImportError:
        raise ImportError(
            "neo4j driver is required. Install it with: pip install atlas_cortex[neo4j]"
        )

    driver = GraphDatabase.driver(uri, auth=auth)

    try:
        with driver.session(database=database) as session:
            # Create constraint
            session.run(
                "CREATE CONSTRAINT atlas_node_id IF NOT EXISTS "
                "FOR (n:AtlasNode) REQUIRE n.id IS UNIQUE"
            )

            # Upsert nodes
            nodes = moc_graph.get("nodes", [])
            doc_id = moc_graph.get("doc_id", "unknown")
            if nodes:
                session.run(
                    """
                    UNWIND $nodes AS node
                    MERGE (n:AtlasNode {id: node.id})
                    ON CREATE SET
                      n.type = node.type,
                      n.title = node.title,
                      n.content = node.content,
                      n.raw_content = node.raw_content,
                      n.content_hash = node.content_hash,
                      n.heading_path = node.heading_path,
                      n.doc_id = $doc_id
                    ON MATCH SET
                      n.content = node.content,
                      n.raw_content = node.raw_content,
                      n.content_hash = node.content_hash
                    """,
                    nodes=nodes,
                    doc_id=doc_id,
                )

            # Upsert edges by type
            edges = moc_graph.get("edges", [])
            edge_types: dict[str, list] = {}
            for edge in edges:
                et = edge.get("type", "related_to")
                if et not in edge_types:
                    edge_types[et] = []
                edge_types[et].append(edge)

            for edge_type, typed_edges in edge_types.items():
                cypher_type = edge_type.upper().replace(" ", "_")
                session.run(
                    f"""
                    UNWIND $edges AS edge
                    MATCH (src:AtlasNode {{id: edge.source}})
                    MATCH (tgt:AtlasNode {{id: edge.target}})
                    MERGE (src)-[r:{cypher_type} {{id: edge.id}}]->(tgt)
                    ON CREATE SET r.method = edge.method
                    """,
                    edges=typed_edges,
                )

            logger.info(
                "Pushed %d nodes and %d edges to Neo4j (%s)",
                len(nodes), len(edges), uri,
            )
    finally:
        driver.close()
