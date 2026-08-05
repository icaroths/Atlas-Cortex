import os
import json
import sys

# Ensure python/ directory is in PYTHONPATH so we can import atlas_cortex
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))

from atlas_cortex import parse_file

def generate_moc(base_dir: str, md_name: str, output_path: str):
    markdown_path = os.path.join(base_dir, md_name)
    print(f"Gerando MOC para {markdown_path}...")
    
    if not os.path.exists(markdown_path):
        print(f"Erro: Arquivo não encontrado - {markdown_path}")
        return False
        
    try:
        # Puxa o grafo determinístico (usará o binário Rust subjacente)
        graph = parse_file(base_dir, md_name)
        
        if "nodes" in graph:
            graph["nodes"].sort(key=lambda x: x.get("id", ""))
        if "edges" in graph:
            graph["edges"].sort(key=lambda x: (x.get("source", ""), x.get("target", "")))
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=4, ensure_ascii=False, sort_keys=True)
            
        print(f"Sucesso: {output_path} atualizado.")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"Falha ao gerar MOC para {markdown_path}: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    
    files_to_process = [
        ("core-protocol_benchmark_corpus.md", "core-protocol_benchmark_corpus.moc.json"),
        ("Paper_Atlas_Cortex_PT.md", "Paper_Atlas_Cortex_PT.moc.json")
    ]
    
    all_success = True
    for md_name, json_name in files_to_process:
        json_path = os.path.join(docs_dir, json_name)
        
        if not generate_moc(docs_dir, md_name, json_path):
            all_success = False
            
    if not all_success:
        sys.exit(1)

if __name__ == "__main__":
    main()
