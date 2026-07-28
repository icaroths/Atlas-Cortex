import os
import json
import subprocess
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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

def retrieve_top_k(corpus: list, query: str, top_k: int = 3) -> list:
    if not corpus:
        return []
    
    docs = corpus + [query]
    vectorizer = TfidfVectorizer(stop_words=None)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
    except ValueError:
        return []

    corpus_matrix = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    similarities = cosine_similarity(query_vector, corpus_matrix).flatten()
    top_indices = np.argsort(similarities)[::-1]
    
    retrieved_texts = []
    for idx in top_indices:
        if similarities[idx] > 0.0:
            retrieved_texts.append(corpus[idx])
        if len(retrieved_texts) == top_k:
            break
            
    return retrieved_texts

def main():
    print("=== Benchmark de Retrieval Quality (Precision/Recall com TF-IDF) ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    moc_path = os.path.join(base_dir, "docs", "Paper_Atlas_Cortex_PT.moc.json")
    qa_path = os.path.join(base_dir, "docs", "benchmarks", "qa_dataset.json")
    
    if not os.path.exists(qa_path):
        print(f"Dataset de QA não encontrado: {qa_path}")
        return

    with open(qa_path, 'r', encoding='utf-8') as f:
        test_suite = json.load(f)

    if not os.path.exists(moc_path):
        print("MOC não encontrado. Gere o MOC do Paper primeiro.")
        return

    with open(moc_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
        
    nodes = moc_data.get("nodes", [])
    atlas_corpus = [node.get("content", "") for node in nodes if node.get("content", "").strip()]
        
    print(f"Verificando {len(test_suite)} perguntas reais contra o MOC do Atlas...\n")
    
    success_count = 0
    top_k = 2
    for idx, test in enumerate(test_suite):
        print(f"[{idx+1}/{len(test_suite)}] Pergunta: {test['question']}")
        
        retrieved = retrieve_top_k(atlas_corpus, test['question'], top_k=top_k)
        context = "\n\n---\n\n".join(retrieved)
        
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
    print(f"Recall Accuracy (Atlas Cortex MOC via TF-IDF): {precision:.1f}% ({success_count}/{len(test_suite)})")
    
    result = {
        "precision_k": precision,
        "success": success_count,
        "total": len(test_suite),
        "methodology": "Scikit-Learn TF-IDF Cosine Similarity + LLM-as-a-judge (qwen2.5-coder:7b)"
    }
    
    out_file = os.path.join(base_dir, "docs", "benchmarks", "retrieval_quality_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

if __name__ == "__main__":
    main()
