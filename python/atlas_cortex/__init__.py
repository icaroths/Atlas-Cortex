import json
import os
import subprocess
import tempfile
from pathlib import Path

__version__ = "1.0.0"

class SecurityError(Exception):
    """Exception raised for security violations like Path Traversal."""

def _get_engine_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe_path = os.path.join(base_dir, "engine", "target", "release", "engine.exe")
    bin_path = os.path.join(base_dir, "engine", "target", "release", "engine")
    if os.path.exists(exe_path):
        return exe_path
    elif os.path.exists(bin_path):
        return bin_path
    raise FileNotFoundError("Engine binary not found.")

def parse_text(text: str, doc_id: str = None):
    """Parses markdown text and returns the generated moc graph."""
    if doc_id is None:
        import hashlib
        doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        
    engine_path = _get_engine_path()
    temp_path = None
    moc_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode='w', encoding='utf-8') as temp_file:
            temp_file.write(text)
            temp_path = temp_file.name
        
        try:
            cmd = [engine_path, temp_path, doc_id]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30 # Timeout requirement to prevent DoS
            )
            if result.returncode != 0:
                raise RuntimeError(f"Engine failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Engine failed: Parse timeout exceeded (30s)")
            
        moc_path = temp_path.replace(".md", ".moc.json")
        if os.path.exists(moc_path):
            with open(moc_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        raise RuntimeError("No .moc.json generated")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        if moc_path and os.path.exists(moc_path):
            try:
                os.remove(moc_path)
            except OSError:
                pass

def parse_file(base_dir, filepath, doc_id=None):
    """Parses a file with strict path traversal and symlink protections."""
    base = Path(base_dir).resolve()
    target = Path(base_dir, filepath).resolve()
    
    if not target.is_relative_to(base):
        raise SecurityError("Path traversal or symlink escape blocked")
        
    if not target.exists():
        raise FileNotFoundError(f"File {target} not found")
        
    return parse_text(target.read_text(encoding='utf-8'), doc_id=doc_id)

def reconcile_graphs(manifest_v1, manifest_v2):
    """
    Compares two graph manifests and returns the reconciliation diff.
    Useful for updating a GraphRAG backend by identifying exactly what changed.
    """
    v1_nodes = {n["id"]: n for n in manifest_v1.get("nodes", [])}
    v2_nodes = {n["id"]: n for n in manifest_v2.get("nodes", [])}
    
    v1_edges = {e["id"]: e for e in manifest_v1.get("edges", []) if "id" in e}
    # If edges don't have ids, we synthesize a hash for reconciliation
    if not v1_edges and manifest_v1.get("edges"):
        import hashlib
        for e in manifest_v1.get("edges", []):
            eid = hashlib.sha256(f"{e.get('source')}-{e.get('target')}-{e.get('type')}".encode()).hexdigest()
            e["id"] = eid
            v1_edges[eid] = e
            
    v2_edges = {e["id"]: e for e in manifest_v2.get("edges", []) if "id" in e}
    if not v2_edges and manifest_v2.get("edges"):
        import hashlib
        for e in manifest_v2.get("edges", []):
            eid = hashlib.sha256(f"{e.get('source')}-{e.get('target')}-{e.get('type')}".encode()).hexdigest()
            e["id"] = eid
            v2_edges[eid] = e

    deleted_node_ids = list(set(v1_nodes.keys()) - set(v2_nodes.keys()))
    added_node_ids = list(set(v2_nodes.keys()) - set(v1_nodes.keys()))
    
    # Updated nodes (same ID, but different content hash)
    updated_nodes = []
    for nid in set(v1_nodes.keys()).intersection(set(v2_nodes.keys())):
        n1 = v1_nodes[nid]
        n2 = v2_nodes[nid]
        # In a real scenario, you'd compare content_hash. If not available, we compare raw_content.
        if n1.get("content_hash") != n2.get("content_hash") or n1.get("raw_content") != n2.get("raw_content"):
            updated_nodes.append(n2)
            
    deleted_edge_ids = list(set(v1_edges.keys()) - set(v2_edges.keys()))
    added_edges = [v2_edges[eid] for eid in set(v2_edges.keys()) - set(v1_edges.keys())]

    return {
        "deleted_node_ids": deleted_node_ids,
        "added_nodes": [v2_nodes[nid] for nid in added_node_ids],
        "updated_nodes": updated_nodes,
        "deleted_edge_ids": deleted_edge_ids,
        "added_edges": added_edges
    }
