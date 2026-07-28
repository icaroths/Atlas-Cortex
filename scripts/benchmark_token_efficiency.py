import os
import json
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import tiktoken
except ImportError:
    print("Por favor, instale o tiktoken: pip install tiktoken")
    exit(1)

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    print("Por favor, instale o langchain-text-splitters: pip install langchain-text-splitters")
    exit(1)

def count_tokens(text: str, model_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(model_name)
    return len(encoding.encode(text))

# Carrega o modelo de forma global para otimizar chamadas
model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_top_k(corpus: list, query: str, top_k: int = 3) -> list:
    """
    Implementação REAL de Embeddings Semânticos e Similaridade de Cosseno.
    Atende ao commit: 'Evolução para SentenceTransformers (all-MiniLM-L6-v2)'
    """
    if not corpus:
        return []
    
    # Gera os embeddings semânticos (vetores densos de 384 dimensões)
    corpus_embeddings = model.encode(corpus)
    query_embedding = model.encode([query])
    
    # Calcula similaridade de cosseno (1D array)
    scores = cosine_similarity(query_embedding, corpus_embeddings).flatten()
    
    # Ordena pelos maiores scores e retorna os top_k textos
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    # Filtra apenas resultados com score > 0.1 (relevância semântica mínima)
    retrieved = [corpus[i] for i in top_indices if scores[i] > 0.1]
    return retrieved

def simulate_atlas_retrieval(nodes: list, query: str, top_k: int = 3) -> int:
    corpus = [node.get("content", "") for node in nodes]
    retrieved = retrieve_top_k(corpus, query, top_k)
    return sum(count_tokens(c) for c in retrieved)

def simulate_langchain_retrieval(chunks: list, query: str, top_k: int = 3) -> int:
    retrieved = retrieve_top_k(chunks, query, top_k)
    return sum(count_tokens(c) for c in retrieved)

def main():
    print("=== Benchmark de Eficiência de Tokens (Sentence Embeddings) ===")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.md")
    moc_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.moc.json")
    qa_path = os.path.join(base_dir, "docs", "benchmarks", "qa_dataset.json")

    if not os.path.exists(qa_path):
        print(f"Dataset de QA não encontrado: {qa_path}")
        return

    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_dataset = json.load(f)

    if not os.path.exists(corpus_path) or not os.path.exists(moc_path):
        print("MOC ou Corpus não encontrados. Gere o MOC primeiro.")
        return

    with open(corpus_path, 'r', encoding='utf-8') as f:
        text = f.read()

    with open(moc_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
    nodes = moc_data.get("nodes", [])

    chunk_size = 1000
    chunk_overlap = 200
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len, is_separator_regex=False)
    chunks = splitter.split_text(text)

    top_k = 3
    total_langchain = 0
    total_atlas = 0

    print(f"Testando {len(qa_dataset)} queries reais de retrieval...\n")

    for i, item in enumerate(qa_dataset):
        q = item["question"]
        l_tokens = simulate_langchain_retrieval(chunks, q, top_k)
        a_tokens = simulate_atlas_retrieval(nodes, q, top_k)

        total_langchain += l_tokens
        total_atlas += a_tokens

    print(f"Resultados Agregados (Top-K = {top_k} | {len(qa_dataset)} queries):")
    print(f"Total Tokens Langchain (Overlap Mecânico): {total_langchain}")
    print(f"Total Tokens Atlas (Nós Atômicos): {total_atlas}")

    diff = total_langchain - total_atlas
    savings = (diff / total_langchain) * 100 if total_langchain > 0 else 0

    print(f"\nEconomia de Tokens Média via Atlas: {diff} tokens ({savings:.2f}%)")

    result = {
        "corpus": "core-protocol_benchmark_corpus.md",
        "queries_tested": len(qa_dataset),
        "top_k": top_k,
        "langchain_tokens_total": total_langchain,
        "atlas_tokens_total": total_atlas,
        "savings_absolute": diff,
        "savings_percentage": round(savings, 2),
        "methodology": "TF-IDF + Cosine Similarity (scikit-learn)"
    }

    out_file = os.path.join(base_dir, "docs", "benchmarks", "token_efficiency_result.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"\n[+] Resultado empírico salvo em: {out_file}")

if __name__ == "__main__":
    main()
