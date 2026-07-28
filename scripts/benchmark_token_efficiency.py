import os
import json
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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def count_tokens(text: str, model_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(model_name)
    return len(encoding.encode(text))

def retrieve_top_k(corpus: list, query: str, top_k: int = 3) -> list:
    if not corpus:
        return []
    
    # Adicionamos a query ao final do corpus para facilitar a vetorização conjunta
    docs = corpus + [query]
    vectorizer = TfidfVectorizer(stop_words=None)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
    except ValueError:
        # Em caso de textos vazios ou stopwords eliminando tudo
        return []

    # Extraímos a matriz do corpus e o vetor da query
    corpus_matrix = tfidf_matrix[:-1]
    query_vector = tfidf_matrix[-1]

    # Calcula similaridade de cosseno
    similarities = cosine_similarity(query_vector, corpus_matrix).flatten()
    
    # Pega os índices com maiores scores
    top_indices = np.argsort(similarities)[::-1]
    
    retrieved_texts = []
    for idx in top_indices:
        if similarities[idx] > 0.0:
            retrieved_texts.append(corpus[idx])
        if len(retrieved_texts) == top_k:
            break
            
    return retrieved_texts

def main():
    print("=== Benchmark de Eficiência de Tokens (TF-IDF Real) ===")
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
    atlas_corpus = [node.get("content", "") for node in nodes if node.get("content", "").strip()]

    chunk_size = 1000
    chunk_overlap = 200
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len, is_separator_regex=False)
    langchain_chunks = splitter.split_text(text)

    top_k = 3
    total_langchain = 0
    total_atlas = 0

    print(f"Testando {len(qa_dataset)} queries reais de retrieval...\n")

    for i, item in enumerate(qa_dataset):
        q = item["question"]
        
        # Recuperação Atlas (Nós Atômicos)
        a_retrieved = retrieve_top_k(atlas_corpus, q, top_k)
        a_tokens = sum(count_tokens(c) for c in a_retrieved)
        
        # Recuperação Langchain (Chunks)
        l_retrieved = retrieve_top_k(langchain_chunks, q, top_k)
        l_tokens = sum(count_tokens(c) for c in l_retrieved)
        
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
        "methodology": "Scikit-Learn TF-IDF Cosine Similarity"
    }

    out_file = os.path.join(base_dir, "docs", "benchmarks", "token_efficiency_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"\n[+] Resultado empírico salvo em: {out_file}")

if __name__ == "__main__":
    main()
