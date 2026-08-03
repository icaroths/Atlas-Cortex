import json
import hashlib
from atlas_cortex import parse_text


def test_atlas_cortex_valid():
    """
    Teste válido de finalidade para o Atlas Cortex.
    Valida: fidelidade, estrutura, conectividade,
    determinismo e utilidade RAG.
    """

    # --------------------------------------------------
    # 1. INPUT CONHECIDO E CONTROLADO
    # --------------------------------------------------

    document = """# Arquitetura

O sistema é composto por três módulos.

## Módulo de Ingestão

Responsável por receber documentos.

Veja também [Módulo de Retrieval](#módulo-de-retrieval).

| Componente | Função |
|---|---|
| Parser | Extrai nós |
| Linker | Gera arestas |

## Módulo de Retrieval

Responsável por buscar contexto relevante.
"""

    doc_id = "documento-teste-001"

    # --------------------------------------------------
    # 2. EXECUÇÃO REAL
    # --------------------------------------------------

    result_1 = parse_text(document, doc_id=doc_id)
    result_2 = parse_text(document, doc_id=doc_id)

    # --------------------------------------------------
    # 3. ASSERTS DE PROPRIEDADES
    # --------------------------------------------------

    errors = []

    # --------------------------------------------------
    # 3.1. SCHEMA
    # --------------------------------------------------

    if result_1.get("schema_version") != "1.0.0":
        errors.append("schema_version ausente ou incorreto")

    if result_1.get("parser_version") is None:
        errors.append("parser_version ausente")

    if result_1.get("doc_id") != doc_id:
        errors.append("doc_id não corresponde ao valor fornecido")

    # --------------------------------------------------
    # 3.2. ESTRUTURA DE NÓS
    # --------------------------------------------------

    nodes = result_1.get("nodes", [])

    if not nodes:
        errors.append("nenhum nó foi gerado")

    node_types = [n.get("type") for n in nodes]

    # Deve conter headings
    if "heading" not in node_types:
        errors.append("nenhum heading foi extraído")

    # Deve conter parágrafos
    if "paragraph" not in node_types:
        errors.append("nenhum paragraph foi extraído")

    # Deve conter tabela
    if "table" not in node_types:
        errors.append("nenhuma tabela foi extraída")

    # Todos os nós devem ter ID
    for node in nodes:
        if not node.get("id"):
            errors.append(f"nó sem id: {node.get('type')}")

        if not node.get("content"):
            errors.append(f"nó sem content: {node.get('type')}")

        if not node.get("content_hash"):
            errors.append(f"nó sem content_hash: {node.get('type')}")

    # --------------------------------------------------
    # 3.3. FIDELIDADE DE CONTEÚDO
    # --------------------------------------------------

    all_content = "\n".join(
        node.get("content", "") for node in nodes
    )

    # Trechos críticos devem estar presentes
    critical_fragments = [
        "Arquitetura",
        "Módulo de Ingestão",
        "Módulo de Retrieval",
        "Parser",
        "Extrai nós",
        "Linker",
        "Gera arestas",
    ]

    for fragment in critical_fragments:
        if fragment not in all_content:
            errors.append(f"fragmento perdido: {fragment}")

    # --------------------------------------------------
    # 3.4. ESTRUTURA DE TABELA
    # --------------------------------------------------

    table_nodes = [n for n in nodes if n.get("type") == "table"]

    if not table_nodes:
        errors.append("nenhum nó de tabela encontrado")
    else:
        table_node = table_nodes[0]
        table_data = table_node.get("table", {})

        if not table_data:
            errors.append("nó de tabela sem dados estruturados")

        header = table_data.get("header", [])
        rows = table_data.get("rows", [])

        if header != ["Componente", "Função"]:
            errors.append(f"header incorreto: {header}")

        if len(rows) != 2:
            errors.append(f"número de linhas incorreto: {len(rows)}")

    # --------------------------------------------------
    # 3.5. CONECTIVIDADE / EDGES
    # --------------------------------------------------

    edges = result_1.get("edges", [])

    if not edges:
        errors.append("nenhuma aresta foi gerada")

    edge_types = [e.get("type") for e in edges]

    # Deve haver arestas hierárquicas
    if "child_of" not in edge_types:
        errors.append("nenhuma aresta child_of encontrada")

    # Deve haver aresta de referência por âncora
    if "references" not in edge_types:
        errors.append("nenhuma aresta references encontrada")

    # Todas as edges devem apontar para nós existentes
    node_ids = {n.get("id") for n in nodes}

    for edge in edges:
        if edge.get("source") not in node_ids:
            errors.append(f"edge com source inexistente: {edge.get('id')}")

        if edge.get("target") not in node_ids:
            errors.append(f"edge com target inexistente: {edge.get('id')}")

    # --------------------------------------------------
    # 3.6. DETERMINISMO
    # --------------------------------------------------

    # Ignore execution metrics that change every run
    def normalize(res):
        import copy
        res = copy.deepcopy(res)
        res.pop("execution_id", None)
        res.pop("generated_at", None)
        res.pop("duration_ms", None)
        return res

    if normalize(result_1) != normalize(result_2):
        errors.append("output não é determinístico entre duas execuções")
        for k in normalize(result_1):
            if normalize(result_1).get(k) != normalize(result_2).get(k):
                print(f"Diff in {k}:")
                print("1:", normalize(result_1).get(k))
                print("2:", normalize(result_2).get(k))

    # IDs devem ser idênticos
    ids_1 = [n.get("id") for n in result_1.get("nodes", [])]
    ids_2 = [n.get("id") for n in result_2.get("nodes", [])]

    if ids_1 != ids_2:
        errors.append("IDs de nós mudaram entre execuções")

    # --------------------------------------------------
    # 3.7. ISOLAMENTO DE DOC_ID
    # --------------------------------------------------

    result_other_doc = parse_text(document, doc_id="outro-documento")

    ids_other = [n.get("id") for n in result_other_doc.get("nodes", [])]

    if ids_1 == ids_other:
        errors.append("doc_id diferente não produziu IDs diferentes")

    # --------------------------------------------------
    # RESULTADO
    # --------------------------------------------------

    if errors:
        print("❌ TESTE FALHOU")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ TESTE PASSOU")
    print(f"  Nós: {len(nodes)}")
    print(f"  Arestas: {len(edges)}")
    print(f"  Tipos de nó: {sorted(set(node_types))}")
    print(f"  Tipos de aresta: {sorted(set(edge_types))}")
    return True

if __name__ == "__main__":
    test_atlas_cortex_valid()
