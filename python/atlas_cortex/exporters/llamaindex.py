"""
Atlas Cortex — LlamaIndex Reader Integration (Fase 13)

Provides a LlamaIndex-compatible Reader that loads Atlas Cortex MOC graphs
and produces LlamaIndex Document nodes with rich metadata, preserving
the semantic graph topology for downstream retrieval.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("atlas_cortex.exporters.llamaindex")


class AtlasCortexReader:
    """
    LlamaIndex Reader for Atlas Cortex MOC graphs.

    Reads .moc.json files or parses documents on-the-fly,
    producing LlamaIndex Document nodes with semantic metadata.

    Usage:
        from atlas_cortex.exporters.llamaindex import AtlasCortexReader

        reader = AtlasCortexReader()
        documents = reader.load_data("path/to/document.moc.json")

        # Or parse and load in one step:
        documents = reader.load_and_parse("path/to/document.md")
    """

    def __init__(self, include_edges_in_metadata: bool = True):
        """
        Args:
            include_edges_in_metadata: If True, edge adjacency info is stored
                                        in each document's metadata.
        """
        self.include_edges_in_metadata = include_edges_in_metadata

    def load_data(self, file_path: str) -> list:
        """
        Load a .moc.json file and produce LlamaIndex Documents.

        Args:
            file_path: Path to a .moc.json file.

        Returns:
            List of LlamaIndex Document objects.
        """
        try:
            from llama_index.core.schema import Document
        except ImportError:
            raise ImportError(
                "llama-index-core is required. "
                "Install it with: pip install atlas_cortex[llamaindex]"
            )

        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            moc_graph = json.load(f)

        return self._graph_to_documents(moc_graph, Document)

    def load_and_parse(self, file_path: str, doc_id: Optional[str] = None) -> list:
        """
        Parse a source document and produce LlamaIndex Documents.

        Supports any format that atlas_cortex.parse_any() supports.

        Args:
            file_path: Path to a source document (.md, .txt, .html, .docx, .epub).
            doc_id: Optional document identifier.

        Returns:
            List of LlamaIndex Document objects.
        """
        try:
            from llama_index.core.schema import Document
        except ImportError:
            raise ImportError(
                "llama-index-core is required. "
                "Install it with: pip install atlas_cortex[llamaindex]"
            )

        from atlas_cortex import parse_any
        moc_graph = parse_any(file_path, doc_id=doc_id)

        return self._graph_to_documents(moc_graph, Document)

    def _graph_to_documents(self, moc_graph: dict, document_cls) -> list:
        """Convert a MOC graph into LlamaIndex Document nodes."""
        documents = []
        doc_id = moc_graph.get("doc_id", "unknown")

        # Pre-compute edge adjacency
        edges_out: dict[str, list[dict]] = {}
        edges_in: dict[str, list[dict]] = {}
        for edge in moc_graph.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            if source not in edges_out:
                edges_out[source] = []
            edges_out[source].append(edge)
            if target not in edges_in:
                edges_in[target] = []
            edges_in[target].append(edge)

        for node in moc_graph.get("nodes", []):
            node_id = node["id"]

            metadata = {
                "atlas_node_id": node_id,
                "atlas_doc_id": doc_id,
                "atlas_node_type": node.get("type", "unknown"),
                "atlas_title": node.get("title", ""),
                "atlas_heading_path": " > ".join(node.get("heading_path", [])),
                "atlas_content_hash": node.get("content_hash", ""),
                "atlas_schema_version": moc_graph.get("schema_version", ""),
                "atlas_parser_version": moc_graph.get("parser_version", ""),
            }

            # Include table summary if present
            if node.get("table"):
                header = node["table"].get("header", [])
                rows = node["table"].get("rows", [])
                metadata["atlas_table_columns"] = ", ".join(header)
                metadata["atlas_table_row_count"] = len(rows)

            # Include provenance if available
            source_info = moc_graph.get("source")
            if source_info:
                metadata["atlas_original_format"] = source_info.get("original_format", "markdown")
                metadata["atlas_converter"] = source_info.get("converter_name", "native")

            if self.include_edges_in_metadata:
                out_edges = edges_out.get(node_id, [])
                in_edges = edges_in.get(node_id, [])

                metadata["atlas_edges_out_count"] = len(out_edges)
                metadata["atlas_edges_in_count"] = len(in_edges)

                # Store compact edge references
                metadata["atlas_related_nodes"] = ", ".join(
                    [f"{e.get('type', 'unknown')}:{e['target'][:16]}" for e in out_edges]
                )

            # Use content as the text, with raw_content as excluded metadata
            text = node.get("content", "")

            doc = document_cls(
                text=text,
                id_=node_id,
                metadata=metadata,
                excluded_llm_metadata_keys=[
                    "atlas_node_id", "atlas_content_hash",
                    "atlas_edges_out_count", "atlas_edges_in_count",
                    "atlas_related_nodes",
                ],
                excluded_embed_metadata_keys=[
                    "atlas_content_hash", "atlas_related_nodes",
                ],
            )
            documents.append(doc)

        logger.info(
            "Loaded %d LlamaIndex documents from MOC graph (doc_id: %s)",
            len(documents), doc_id,
        )

        return documents
