import argparse
import json
import os


def parse_markdown_topologically(text):
    """
    Simula o Roteamento Semântico Atômico (Nível 1) do Atlas Cortex.
    Quebra o texto em nós apenas baseados em headers (##, ###, etc) sem usar overlap de caracteres.
    """
    lines = text.split('\n')
    nodes = []
    current_node = {"id": 0, "title": "root", "content": ""}
    node_id = 0
    
    for line in lines:
        if line.startswith('#'):
            # Salva o nó anterior se tiver conteúdo
            if current_node["content"].strip():
                nodes.append(current_node)
            
            node_id += 1
            current_node = {
                "id": node_id,
                "title": line.strip(),
                "content": line + "\n"
            }
        else:
            current_node["content"] += line + "\n"
            
    if current_node["content"].strip():
        nodes.append(current_node)
        
    return nodes

def main():
    parser = argparse.ArgumentParser(description="Mock Atlas Cortex Ingestor")
    parser.add_argument("--path", required=True, help="Path to markdown file or directory")
    args = parser.parse_args()
    
    if os.path.isfile(args.path):
        files = [args.path]
    else:
        files = [os.path.join(args.path, f) for f in os.listdir(args.path) if f.endswith('.md')]
        
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            
        nodes = parse_markdown_topologically(text)
        moc_path = filepath.replace('.md', '.moc.json')
        
        with open(moc_path, 'w', encoding='utf-8') as f:
            json.dump({"nodes": nodes}, f, ensure_ascii=False, indent=2)
            
        print(f"Ingestão Atômica completa: {len(nodes)} nós semânticos gerados em {moc_path}")

if __name__ == "__main__":
    main()
