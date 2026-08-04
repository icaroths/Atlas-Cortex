import os
import sys
import subprocess
import json

def run_in_env(env_dir, text):
    tmp_txt = os.path.join(env_dir, "temp_bench_input.md")
    with open(tmp_txt, "w", encoding="utf-8") as f:
        f.write(text)

    script = f"""
import sys, json, os, time
sys.path.insert(0, r"{env_dir}\\python")
from atlas_cortex import parse_text

with open(r"{tmp_txt}", "r", encoding="utf-8") as f:
    text = f.read()

t0 = time.perf_counter()
g = parse_text(text, doc_id="benchmark_doc")
t1 = time.perf_counter()

res = {{
    "execution_time_ms": round((t1 - t0) * 1000.0, 2),
    "graph": g
}}
print(json.dumps(res))
"""
    try:
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    finally:
        if os.path.exists(tmp_txt):
            os.remove(tmp_txt)

def main():
    dev_dir = r"i:\Atlas-Cortex-Dev"
    rel_dir = r"i:\Atlas-Cortex-Release"

    large_text = "\n\n".join([f"## Secao {i}\n\nEste eh o paragrafo de conteudo numero {i} contendo informacoes semanticas relevantes para a avaliacao de estresse e extensao de capacidade do motor Atlas Cortex V2." for i in range(1, 450)])

    char_count = len(large_text)
    raw_tokens_est = int(char_count / 4)
    # Sliding window RAG (15% overlap + 15% boundary duplication = 30% overhead)
    traditional_rag_tokens = int(raw_tokens_est * 1.30)

    print("Executando Benchmark Isolado no DEV (Enterprise 100%)...")
    res_dev = run_in_env(dev_dir, large_text)
    g_dev = res_dev["graph"]
    time_dev_ms = res_dev["execution_time_ms"]

    print("Executando Benchmark Isolado no RELEASE (Evaluation 750 Quota)...")
    res_rel = run_in_env(rel_dir, large_text)
    g_rel = res_rel["graph"]
    time_rel_ms = res_rel["execution_time_ms"]

    nodes_dev = g_dev.get("nodes", [])
    edges_dev = g_dev.get("edges", [])
    dev_tokens = sum(int(len(n.get("content", "")) / 4) for n in nodes_dev)
    dev_savings = round(((traditional_rag_tokens - dev_tokens) / traditional_rag_tokens) * 100.0, 2)
    dev_throughput = round(len(nodes_dev) / (time_dev_ms / 1000.0), 2) if time_dev_ms > 0 else 0

    nodes_rel = g_rel.get("nodes", [])
    edges_rel = g_rel.get("edges", [])
    rel_tokens = sum(int(len(n.get("content", "")) / 4) for n in nodes_rel)
    rel_savings = round(((traditional_rag_tokens - rel_tokens) / traditional_rag_tokens) * 100.0, 2)
    rel_throughput = round(len(nodes_rel) / (time_rel_ms / 1000.0), 2) if time_rel_ms > 0 else 0

    orig_n = g_rel.get("original_node_count", len(nodes_rel))
    extrapolated_nodes = orig_n
    extrapolated_tokens_est = int((rel_tokens / len(nodes_rel)) * orig_n) if len(nodes_rel) > 0 else 0
    extrapolated_savings_est = round(((traditional_rag_tokens - extrapolated_tokens_est) / traditional_rag_tokens) * 100.0, 2)

    report = {
        "corpus_info": {
            "title": "Corpus Sintetico de Carga Massiva (898 Nos Totais)",
            "characters": char_count,
            "raw_tokens_estimate": raw_tokens_est,
            "traditional_rag_tokens_15pct_overlap": traditional_rag_tokens
        },
        "dev_environment_enterprise_100pct": {
            "execution_time_ms": time_dev_ms,
            "nodes_generated": len(nodes_dev),
            "edges_generated": len(edges_dev),
            "is_truncated": g_dev.get("truncated", False),
            "atlas_tokens": dev_tokens,
            "actual_token_savings_percent": dev_savings,
            "throughput_nodes_sec": dev_throughput
        },
        "evaluation_environment_quota_750": {
            "execution_time_ms": time_rel_ms,
            "nodes_generated": len(nodes_rel),
            "edges_generated": len(edges_rel),
            "is_truncated": g_rel.get("truncated", False),
            "original_node_count": g_rel.get("original_node_count"),
            "truncated_node_count": g_rel.get("truncated_node_count"),
            "atlas_tokens_750_nodes": rel_tokens,
            "real_token_savings_750_nodes": rel_savings,
            "throughput_nodes_sec": rel_throughput,
            "extrapolation_model_to_100pct": {
                "extrapolated_nodes": extrapolated_nodes,
                "extrapolated_tokens_est": extrapolated_tokens_est,
                "extrapolated_savings_percent_est": extrapolated_savings_est
            }
        }
    }

    out_file_dev = os.path.join(dev_dir, "docs", "benchmarks", "dual_math_benchmark_results.json")
    out_file_rel = os.path.join(rel_dir, "docs", "benchmarks", "dual_math_benchmark_results.json")

    for f_path in [out_file_dev, out_file_rel]:
        os.makedirs(os.path.dirname(f_path), exist_ok=True)
        with open(f_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

    print("=================================================================")
    print("BENCHMARK COMPARATIVO DUAL CONCLUIDO!")
    print(f"Dev (100% Unrestricted): {len(nodes_dev)} nos em {time_dev_ms}ms (Truncated: {g_dev.get('truncated')})")
    print(f"Evaluation (750 Limit):  {len(nodes_rel)} nos em {time_rel_ms}ms (Truncated: {g_rel.get('truncated')})")
    print("=================================================================")

if __name__ == "__main__":
    main()
