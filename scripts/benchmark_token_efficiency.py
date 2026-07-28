import os
import json
import re
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

def extract_keywords(text: str):
    words = re.findall(r'\w+', text.lower())
    stopwords = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "em", "no", "na", "que", "para", "com", "qual", "como", "por", "sobre", "é", "são", "e", "ou"}
    return set([w for w in words if w not in stopwords and len(w) > 2])

def score_text(text: str, query_keywords: set) -> int:
    text_words = re.findall(r'\w+', text.lower())
    score = sum(1 for w in text_words if w in query_keywords)
    return score

def simulate_atlas_retrieval(nodes: list, query: str, top_k: int = 3) -> int:
    keywords = extract_keywords(query)
    scored_nodes = []
    for node in nodes:
        content = node.get("content", "")
        score = score_text(content, keywords)
        scored_nodes.append((score, content))
        
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    retrieved = [n[1] for n in scored_nodes[:top_k]]
    return sum(count_tokens(c) for c in retrieved)

def simulate_langchain_retrieval(chunks: list, query: str, top_k: int = 3) -> int:
    keywords = extract_keywords(query)
    scored_chunks = []
    for chunk in chunks:
        score = score_text(chunk, keywords)
        scored_chunks.append((score, chunk))
        
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    retrieved = [c[1] for c in scored_chunks[:top_k]]
    return sum(count_tokens(c) for c in retrieved)

def main():
    print("=== Benchmark de Eficiência de Tokens (Semântico Real) ===")
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
        "savings_percentage": round(savings, 2)
    }

    out_file = os.path.join(base_dir, "docs", "benchmarks", "token_efficiency_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"\n[+] Resultado empírico salvo em: {out_file}")

if __name__ == "__main__":
    main()
