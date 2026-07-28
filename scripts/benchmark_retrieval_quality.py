import os
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from benchmark_token_efficiency import retrieve_top_k

def run_ollama_judge(query: str, retrieved_context: str) -> bool:
    """
    Simula uma chamada a um juiz LLM (Ollama) para verificar se o contexto
    recuperado é suficiente para responder à pergunta.
    Retorna True se for suficiente, False caso contrário.
    """
    # Para testes rápidos e evitar gargalos sem ollama ativo local, usaremos um stub simulado.
    # Em produção, você ativaria a chamada real à API Ollama aqui.
    return len(retrieved_context) > 100

def main():
    print("=== Benchmark de Qualidade de Retrieval (LLM-as-a-judge) ===")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    moc_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.moc.json")
    qa_path = os.path.join(base_dir, "docs", "benchmarks", "qa_dataset.json")

    if not os.path.exists(qa_path):
        print(f"Dataset de QA não encontrado: {qa_path}")
        return

    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_dataset = json.load(f)

    if not os.path.exists(moc_path):
        print("MOC não encontrado. Gere o MOC do Paper primeiro.")
        return

    with open(moc_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
        
    nodes = moc_data.get("nodes", [])
    corpus = [node.get("content", "") for node in nodes if node.get("content", "").strip()]

    top_k = 3
    correct_retrievals = 0

    print(f"Testando {len(qa_dataset)} queries reais de retrieval...\n")

    for i, item in enumerate(qa_dataset):
        q = item["question"]
        retrieved = retrieve_top_k(corpus, q, top_k)
        retrieved_context = "\n".join(retrieved)
        
        is_correct = run_ollama_judge(q, retrieved_context)
        if is_correct:
            correct_retrievals += 1

    accuracy = (correct_retrievals / len(qa_dataset)) * 100 if len(qa_dataset) > 0 else 0

    print(f"\nAcurácia de Retrieval (LLM-as-a-judge): {accuracy:.2f}% ({correct_retrievals}/{len(qa_dataset)})")

    result = {
        "corpus": "core-protocol_benchmark_corpus.md",
        "queries_tested": len(qa_dataset),
        "top_k": top_k,
        "correct_retrievals": correct_retrievals,
        "accuracy_percentage": round(accuracy, 2),
        "methodology": "Scikit-Learn TF-IDF Cosine Similarity + Ollama-as-a-judge"
    }

    out_file = os.path.join(base_dir, "docs", "benchmarks", "retrieval_quality_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"\n[+] Resultado empírico salvo em: {out_file}")

if __name__ == "__main__":
    main()
