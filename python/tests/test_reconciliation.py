import pytest
from atlas_cortex import parse_text, reconcile_graphs

def test_reconcile_graphs_added_node():
    doc1 = "# Arquitetura\n\nTexto original."
    doc2 = "# Arquitetura\n\nTexto original.\n\n## Nova Seção\n\nNovo texto."
    
    g1 = parse_text(doc1, doc_id="reconcile1")
    g2 = parse_text(doc2, doc_id="reconcile1")
    
    diff = reconcile_graphs(g1, g2)
    
    # Houve adição de nós
    assert len(diff["added_nodes"]) > 0
    # Houve também atualização de IDs devido à sequência deslocada
    # (dependendo de como o ID é gerado, o texto original pode ter recebido um novo ID)

def test_reconcile_graphs_modified_node():
    doc1 = "# Título\n\nTexto antigo."
    doc2 = "# Título\n\nTexto novo modificado."
    
    g1 = parse_text(doc1, doc_id="mod")
    g2 = parse_text(doc2, doc_id="mod")
    
    # Como as sequencias não mudaram (são 2 nós em ambos), os IDs devem ser os mesmos
    # Mas o content_hash mudou, então deve vir em updated_nodes
    diff = reconcile_graphs(g1, g2)
    
    assert len(diff["updated_nodes"]) == 1
    assert diff["updated_nodes"][0]["raw_content"] == "Texto novo modificado."
    assert len(diff["added_nodes"]) == 0
    assert len(diff["deleted_node_ids"]) == 0

def test_reconcile_graphs_deleted_node():
    doc1 = "# Titulo\n\nParagrafo 1\n\n## Sub\n\nParagrafo 2"
    doc2 = "# Titulo\n\nParagrafo 1"
    
    g1 = parse_text(doc1, doc_id="del")
    g2 = parse_text(doc2, doc_id="del")
    
    diff = reconcile_graphs(g1, g2)
    
    assert len(diff["deleted_node_ids"]) == 2
