import os
import json
import argparse

def generate_cypher_from_moc(moc_path: str, output_path: str):
    """
    Lê o JSON do Atlas Cortex (.moc.json) gerado pelo motor Tree-Sitter
    e converte os nós topológicos atômicos em comandos Cypher prontos 
    para injeção em um banco Neo4j (GraphRAG).
    """
    if not os.path.exists(moc_path):
        print(f"Erro: Arquivo MOC não encontrado em {moc_path}")
        return

    with open(moc_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    
    cypher_commands = []
    cypher_commands.append("// Limpeza inicial (apenas para ambiente de dev/teste)")
    cypher_commands.append("MATCH (n:AtlasNode) DETACH DELETE n;")
    cypher_commands.append("")

    # Criando os nós
    cypher_commands.append("// Injeção de Nós Semânticos (Atomic Knowledge)")
    for node in nodes:
        node_id = node.get("id")
        title = node.get("title", "").replace("'", "\\'").replace('"', '\\"')
        content = node.get("content", "").replace("'", "\\'").replace('"', '\\"')
        
        cmd = f"""CREATE (n{node_id}:AtlasNode {{
    id: {node_id},
    title: "{title}",
    content: "{content}"
}});"""
        cypher_commands.append(cmd)

    cypher_commands.append("")
    cypher_commands.append("// Criando as Arestas Topológicas (Sequência de Fluxo Documental)")
    # Estabelece NEXT_SECTION
    for i in range(len(nodes) - 1):
        n_current = nodes[i].get("id")
        n_next = nodes[i+1].get("id")
        
        edge_cmd = f"MATCH (a:AtlasNode {{id: {n_current}}}), (b:AtlasNode {{id: {n_next}}}) CREATE (a)-[:NEXT_SECTION]->(b);"
        cypher_commands.append(edge_cmd)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(cypher_commands))

    print(f"Pipeline GraphRAG gerou {len(nodes)} nós e conectou as arestas.")
    print(f"Arquivo Cypher exportado para: {output_path}")
    print("Para injetar no Neo4j, utilize o driver Python oficial ou 'cypher-shell -f arquivo.cypher'")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_moc = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.moc.json")
    default_out = os.path.join(base_dir, "docs", "benchmarks", "graphrag_injection.cypher")
    
    parser = argparse.ArgumentParser(description="Atlas Cortex -> Neo4j (GraphRAG) Pipeline")
    parser.add_argument("--moc", default=default_moc, help="Caminho do arquivo .moc.json")
    parser.add_argument("--out", default=default_out, help="Caminho de saída para o .cypher")
    
    args = parser.parse_args()
    generate_cypher_from_moc(args.moc, args.out)
