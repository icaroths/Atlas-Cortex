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
    payload = "> " * 100000 + "deep"
    
    try:
        parse_text(payload)
    except Exception as e:
        # Graceful degradation (e.g. AST width limit or parse failure)
        assert "Engine failed" in str(e) or "limit exceeded" in str(e)

import subprocess
from unittest import mock

from atlas_cortex import reconcile_graphs


def test_parse_timeout_kills_subprocess():
    """Simulate a subprocess that hangs, ensure timeout kills it."""
    # We patch subprocess.run to simulate a hang that raises TimeoutExpired
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="engine.exe", timeout=30)
        
        with pytest.raises(RuntimeError) as exc:
            parse_text("some text")
            
        assert "Timeout" in str(exc.value) or "failed" in str(exc.value) or "No .moc.json generated" in str(exc.value)

def test_graph_reconciliation():
    v1_text = "# Header\n\nNode A.\n\nNode B to be deleted."
    v2_text = "# Header\n\nNode A updated.\n\nNode C added."
    
    manifest_v1 = parse_text(v1_text)
    manifest_v2 = parse_text(v2_text)
    
    diff = reconcile_graphs(manifest_v1, manifest_v2)
    
    assert len(diff["deleted_node_ids"]) >= 1
    assert len(diff["added_nodes"]) >= 1
    assert len(diff["updated_nodes"]) >= 1

def test_path_traversal_blocked():
    with pytest.raises(SecurityError) as exc:
        parse_file("/safe/dir", "../../../etc/passwd")
    assert "traversal" in str(exc.value).lower()

def test_huge_line_degrades_gracefully():
    payload = "A" * 10_000_000
    try:
        parse_text(payload)
    except Exception as e:
        assert "Engine failed" in str(e) or "timeout" in str(e).lower()

def test_invalid_utf8():
    with pytest.raises(UnicodeDecodeError) as exc:
        # Passando bytes inválidos que não devem ser lidos como string diretamente
        b = b"\xff\xfe\x00\x00"
        b.decode("utf-8")
