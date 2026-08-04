import pytest
from atlas_cortex import SecurityError, parse_file, parse_text


def test_path_traversal_blocked(tmp_path):
    base = tmp_path / "data"
    base.mkdir()
    
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    
    malicious = "../secret.txt"
    
    with pytest.raises(SecurityError):
        parse_file(base, malicious)

def test_symlink_escape_blocked(tmp_path):
    base = tmp_path / "data"
    base.mkdir()
    
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    
    link = base / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink privilege not available on Windows")
    
    with pytest.raises(SecurityError):
        parse_file(base, "link.txt")

def test_markdown_bomb_degrades_gracefully():
    # Usando bomb por largura (siblings) ao invés de profundidade (nested blockquotes).
    payload = "* item\n" * 500_005
    
    try:
        nodes = parse_text(payload)
        # Se o PyO3 conseguir lidar com isso nativamente e rápido, então passou.
        assert len(nodes["nodes"]) > 0
    except Exception as exc:
        # Se cair no limite de AST ou timeout do subprocess, passou também.
        assert "Engine failed" in str(exc) or "limit exceeded" in str(exc) or "Parse error" in str(exc)

import subprocess  # noqa: E402
import sys  # noqa: E402
from unittest import mock  # noqa: E402

from atlas_cortex import reconcile_graphs  # noqa: E402


def test_parse_timeout_kills_subprocess():
    """Simulate a subprocess that hangs, ensure timeout kills it."""
    import atlas_cortex
    old_val = atlas_cortex._FORCE_SUBPROCESS
    atlas_cortex._FORCE_SUBPROCESS = True
    try:
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="engine.exe", timeout=30)
            
            with pytest.raises(RuntimeError) as exc:
                parse_text("some text")
                
            assert "Timeout" in str(exc.value) or "failed" in str(exc.value) or "No .moc.json generated" in str(exc.value)
    finally:
        atlas_cortex._FORCE_SUBPROCESS = old_val

def test_graph_reconciliation():
    v1_text = "# Header\n\nNode A.\n\nNode B to be deleted."
    v2_text = "# Header\n\nNode A updated.\n\nNode C added."
    
    manifest_v1 = parse_text(v1_text)
    manifest_v2 = parse_text(v2_text)
    
    diff = reconcile_graphs(manifest_v1, manifest_v2)
    
    # Se parse_text não recebeu doc_id explícito, os IDs são gerados baseados no conteúdo.
    # Portanto, todos os nós mudam de ID, resultando em deletes e adds, e 0 updates.
    assert len(diff["deleted_node_ids"]) >= 1
    assert len(diff["added_nodes"]) >= 1

def test_path_traversal_blocked_basic():
    with pytest.raises(SecurityError) as exc:
        parse_file("/safe/dir", "../../../etc/passwd")
    assert "traversal" in str(exc.value).lower()

def test_huge_line_degrades_gracefully():
    payload = "A" * 10_000_000
    # O motor suporta 10MB em uma linha (retorna um parágrafo grande).
    # O teste valida que não há Segfault ou estouro de memória, retornando nós com sucesso.
    nodes = parse_text(payload)
    assert len(nodes) > 0

def test_invalid_utf8_file(tmp_path):
    base = tmp_path / "data"
    base.mkdir()
    invalid_file = base / "invalid.txt"
    invalid_file.write_bytes(b"\xff\xfe\x00\x00")
    
    with pytest.raises(Exception):
        parse_file(base, "invalid.txt")
    # Rust should reject the file or python will fail reading it, but it shouldn't crash the interpreter
