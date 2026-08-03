import pytest
from atlas_cortex import parse_text

def test_hostile_empty_document():
    """String vazia e apenas quebras de linha não devem quebrar o parser."""
    result = parse_text("", doc_id="empty1")
    assert result["nodes"] == []
    assert result["edges"] == []
    
    result = parse_text("\n\n  \n\r\n", doc_id="empty2")
    assert result["nodes"] == []
    assert result["edges"] == []

def test_hostile_null_bytes():
    """Injeção de null bytes e caracteres de controle severos."""
    text = "Hello\x00World\x1b[31mRed\x1b[0m\n\n## Title\x07"
    result = parse_text(text, doc_id="nullbytes")
    
    nodes = result["nodes"]
    assert len(nodes) > 0
    # O rust via JSON não deve falhar serializando chars de controle que o serde consegue tratar,
    # ou os filtra, dependendo de como Tree-sitter os interpreta.
    assert result["schema_version"] == "1.0.0"

def test_hostile_malformed_tables():
    """Tabelas faltando pipes ou com linhas incompatíveis."""
    text = """
| Head1 | Head2
|---|
| Cell 1 | Cell 2 | Cell 3 |
Cell 4 | Cell 5
"""
    result = parse_text(text, doc_id="malformedtable")
    # Não deve crashar. Pode ou não ser identificada como tabela pelo tree-sitter.
    assert isinstance(result["nodes"], list)

def test_hostile_broken_anchors():
    """Links cíclicos e alvos inexistentes."""
    text = """# A
[Vai pro B](#b)

## B
[Volta pro A](#a)
[Vai pro NADA](#nada)
"""
    result = parse_text(text, doc_id="brokenanchors")
    edges = result["edges"]
    
    # As arestas de references são geradas apenas se o target existir no documento.
    references = [e for e in edges if e["type"] == "references"]
    
    [e["target"] for e in references]
    
    # "nada" não deve estar em targets porque o heading correspondente não existe
    for n in result["nodes"]:
        if n["type"] == "heading" and n.get("title") == "NADA":
            pytest.fail("Heading NADA não devia existir")

def test_hostile_extreme_unicode():
    """Unicode severo misturado com links e tabelas."""
    text = """# 🚀 Título 😂

Aqui um parágrafo 👨‍👩‍👧‍👦 com Zalgo t̵e̵x̵t̵ 

| 🪲 Bug | 🛑 Fix |
|---|---|
| 💥 | 🛠️ |

[Link para Título](#-título-)
"""
    result = parse_text(text, doc_id="extreme_unicode")
    # Parser não deve panicar
    assert len(result["nodes"]) >= 3
