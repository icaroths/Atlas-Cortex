import os
import json
import subprocess
import re

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

def extract_keywords(text: str):
    words = re.findall(r'\w+', text.lower())
    stopwords = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "em", "no", "na", "que", "para", "com", "qual", "como", "por", "sobre", "é", "são", "e", "ou"}
    return set([w for w in words if w not in stopwords and len(w) > 2])

def score_text(text: str, query_keywords: set) -> int:
    text_words = re.findall(r'\w+', text.lower())
    score = sum(1 for w in text_words if w in query_keywords)
    return score

def load_atlas_context(moc_json_path: str, query: str, top_k: int = 3) -> str:
    if not os.path.exists(moc_json_path):
        return ""
        
    with open(moc_json_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
        
    nodes = moc_data.get("nodes", [])
    keywords = extract_keywords(query)
    
    scored_nodes = []
    for node in nodes:
        content = node.get("content", "")
        score = score_text(content, keywords)
        scored_nodes.append((score, content))
        
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    context_chunks = [node[1] for node in scored_nodes[:top_k] if node[0] > 0]
    return "\n\n---\n\n".join(context_chunks)

def main():
    print("=== Benchmark de Retrieval Quality (Precision/Recall) ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    moc_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.moc.json")
    qa_path = os.path.join(base_dir, "docs", "benchmarks", "qa_dataset.json")
    
    if not os.path.exists(qa_path):
        print(f"Dataset de QA não encontrado: {qa_path}")
        return

    with open(qa_path, 'r', encoding='utf-8') as f:
        test_suite = json.load(f)
        
    print(f"Verificando {len(test_suite)} perguntas reais contra o MOC do Atlas...\n")
    
    success_count = 0
    for idx, test in enumerate(test_suite):
        print(f"[{idx+1}/{len(test_suite)}] Pergunta: {test['question']}")
        
        context = load_atlas_context(moc_path, test['question'], top_k=2)
        if not context:
            print("  -> Falha: MOC não encontrado ou sem correspondência.")
            continue
            
        is_successful = run_ollama_judge(test['question'], context)
        
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
