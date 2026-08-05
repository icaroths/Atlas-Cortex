from atlas_cortex import parse_text


def test_schema_version_present():
    out = parse_text("# A")
    assert "schema_version" in out, "schema_version ausente"
    assert "parser_version" in out, "parser_version ausente"
    assert out["schema_version"] == "1.0.0"

def test_table_parsing_structured():
    md = """| Nome | Papel |
|---|---|
| Atlas | Parser |"""
    out = parse_text(md)
    nodes = out.get("nodes", [])
    table_nodes = [n for n in nodes if n.get("type") == "table"]
    assert len(table_nodes) == 1
    table_data = table_nodes[0].get("table")
    assert table_data is not None
    assert "Nome" in table_data.get("header", [])
    assert ["Atlas", "Parser"] in table_data.get("rows", [])

def test_hierarchical_edges_present():
    md = """# A

Veja [B](#b).

## B"""
    out = parse_text(md)
    edges = out.get("edges", [])
    child_of_edges = [e for e in edges if e.get("type") == "child_of"]
    assert len(child_of_edges) > 0
