import os
import json
import subprocess

def run_ollama_judge(question: str, context: str) -> bool:
    """
    Usa o qwen2.5-coder:7b via Ollama (offline e custo zero) como LLM-as-a-Judge.
    Ele avalia se o contexto fornecido responde a pergunta.
    """
    prompt = f"""Você é um avaliador de RAG (LLM-as-a-Judge).
Responda APENAS com "SIM" ou "NAO".
O contexto abaixo contém informações suficientes para responder a seguinte pergunta?

Pergunta: {question}

Contexto:
{context}

Avaliação (SIM/NAO):"""

    try:
        # Comando para rodar ollama via CLI
        result = subprocess.run(
            ['ollama', 'run', 'qwen2.5-coder:7b', prompt],
            capture_output=True,
            text=True,
            timeout=120
        )
        response = result.stdout.strip().upper()
        return "SIM" in response
    except Exception as e:
        print(f"Erro ao chamar Ollama: {e}")
        return False

def load_atlas_context(moc_json_path: str, query_terms: list, top_k: int = 3) -> str:
    """
    Simula um retrieval super simples sobre o MOC do Atlas buscando por termos chave.
    """
    if not os.path.exists(moc_json_path):
        return ""
        
    with open(moc_json_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
        
    nodes = moc_data.get("nodes", [])
    
    # Retrieval de brinquedo: conta hits de termos e pega os top_k
    scored_nodes = []
    for node in nodes:
        content = node.get("content", "").lower()
        score = sum(1 for term in query_terms if term.lower() in content)
        scored_nodes.append((score, node.get("content", "")))
        
    # Ordena pelo score decrescente
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    
    # Monta o contexto final combinando os K melhores
    context_chunks = [node[1] for node in scored_nodes[:top_k] if node[0] > 0]
    return "\n\n---\n\n".join(context_chunks)

def main():
    print("=== Benchmark de Retrieval Quality (Precision/Recall) ===")
    
    moc_path = r"i:\Aurelius_Workspace\.agents\rules\core-protocol.moc.json"
    
    # Bateria de perguntas curadas baseadas no Core Protocol
    test_suite = [
        {
            "q": "O que o agente deve anunciar obrigatoriamente antes de usar uma skill?",
            "terms": ["announce", "skill", "Using skill", "MANDATORY"]
        },
        {
            "q": "Qual arquivo deve ser lido no início da sessão para carregar convenções do projeto e decisões?",
            "terms": ["session start", "MEMORY.md", "persistent project conventions"]
        },
        {
            "q": "Quais são as pastas que devem ser verificadas antes de modificar qualquer arquivo para dependências?",
            "terms": ["CODEBASE.md", "File Dependencies", "dependent files"]
        }
    ]
    
    print(f"Verificando {len(test_suite)} perguntas contra o MOC do Atlas...\n")
    
    success_count = 0
    for idx, test in enumerate(test_suite):
        print(f"[{idx+1}/{len(test_suite)}] Pergunta: {test['q']}")
        
        context = load_atlas_context(moc_path, test['terms'], top_k=2)
        if not context:
            print("  -> Falha: MOC não encontrado ou contexto vazio.")
            continue
            
        is_successful = run_ollama_judge(test['q'], context)
        
        if is_successful:
            print("  -> Avaliação: PASSOU (O contexto responde a pergunta)")
            success_count += 1
        else:
            print("  -> Avaliação: FALHOU (O contexto não é suficiente)")
            
    print("\n--- Resultados Finais ---")
    precision = (success_count / len(test_suite)) * 100
    print(f"Recall Accuracy (Atlas Cortex MOC): {precision:.1f}% ({success_count}/{len(test_suite)})")
    print("Nota: Este script requer o Ollama local rodando qwen2.5-coder:7b para o LLM-as-a-Judge.")

if __name__ == "__main__":
    main()
