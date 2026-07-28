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

def count_tokens(text: str, model_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(model_name)
    return len(encoding.encode(text))

def simulate_atlas_retrieval(moc_json_path: str, top_k: int = 3) -> int:
    """
    Simula o retrieval via Atlas Cortex (MOC).
    Nesta simulação, lemos o MOC gerado e resgatamos os top K nós.
    Como o Atlas não usa overlap, contamos os tokens brutos dos K nós.
    """
    if not os.path.exists(moc_json_path):
        print(f"MOC não encontrado em {moc_json_path}. Execute o Atlas Cortex CLI primeiro.")
        return 0
        
    with open(moc_json_path, 'r', encoding='utf-8') as f:
        moc_data = json.load(f)
        
    nodes = moc_data.get("nodes", [])
    if not nodes:
        return 0
        
    # Pega os primeiros K nós (simulando uma busca vetorial perfeita)
    retrieved_nodes = nodes[:top_k]
    
    total_tokens = 0
    for node in retrieved_nodes:
        content = node.get("content", "")
        total_tokens += count_tokens(content)
        
    return total_tokens

def simulate_langchain_retrieval(corpus_path: str, chunk_size: int = 500, chunk_overlap: int = 100, top_k: int = 3) -> int:
    """
    Simula o RAG tradicional com RecursiveCharacterTextSplitter.
    """
    if not os.path.exists(corpus_path):
        print(f"Corpus não encontrado em {corpus_path}")
        return 0
        
    with open(corpus_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = splitter.split_text(text)
    if not chunks:
        return 0
        
    # Pega os primeiros K chunks
    retrieved_chunks = chunks[:top_k]
    
    total_tokens = 0
    for chunk in retrieved_chunks:
        total_tokens += count_tokens(chunk)
        
    return total_tokens

def main():
    print("=== Benchmark de Eficiência de Tokens (Zero-Overlap) ===")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.md")
    moc_path = os.path.join(base_dir, "docs", "core-protocol_benchmark_corpus.moc.json")
    
    print(f"1. Analisando Corpus: {corpus_path}")
    
    # Parâmetros
    top_k = 3
    chunk_size = 1000  # caracteres
    chunk_overlap = 200 # 20% overlap
    
    tokens_langchain = simulate_langchain_retrieval(corpus_path, chunk_size, chunk_overlap, top_k)
    tokens_atlas = simulate_atlas_retrieval(moc_path, top_k)
    
    print("\nResultados (Top-K = {}):".format(top_k))
    print(f"Tokens gastos no Langchain (20% overlap): {tokens_langchain} tokens")
    
    result = {
        "corpus": "core-protocol_benchmark_corpus.md",
        "top_k": top_k,
        "langchain_tokens": tokens_langchain,
        "atlas_tokens": tokens_atlas,
        "savings_absolute": 0,
        "savings_percentage": 0.0
    }
    
    if tokens_atlas > 0:
        print(f"Tokens gastos no Atlas Cortex (0% overlap): {tokens_atlas} tokens")
        
        diff = tokens_langchain - tokens_atlas
        savings = (diff / tokens_langchain) * 100 if tokens_langchain > 0 else 0
        
        print(f"\nEconomia de Tokens via Atlas: {diff} tokens ({savings:.2f}%)")
        
        result["savings_absolute"] = diff
        result["savings_percentage"] = round(savings, 2)
        
        # Salva a evidência do benchmark
        out_file = os.path.join(base_dir, "docs", "benchmarks", "token_efficiency_result.json")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
        print(f"\n[+] Resultado empírico salvo em: {out_file}")
    else:
        print("\nPara ver o comparativo do Atlas, gere primeiro o MOC do corpus utilizando o simulador open-source.")
        print(f"Ex: python scripts/mock_atlas_ingestor.py --path docs/core-protocol_benchmark_corpus.md")

if __name__ == "__main__":
    main()
