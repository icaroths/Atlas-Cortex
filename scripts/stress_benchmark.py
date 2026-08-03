import json
import time
import os
import gc
from pathlib import Path

# Ajuste do path para o módulo nativo
import sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from python.atlas_cortex import parse_text

import uuid

def generate_synthetic_markdown(target_size_mb: int) -> str:
    """Gera um texto Markdown repetitivo até atingir o tamanho estimado em MB."""
    target_bytes = target_size_mb * 1024 * 1024
    
    # Gera array e junta (mais rapido que += string)
    doc = "# Stress Test - Mass Generation\n\n"
    parts = []
    current_bytes = len(doc)
    
    while current_bytes < target_bytes:
        unique_word = uuid.uuid4().hex
        block = (
            f"## {unique_word}\n\n"
            "Este eh um paragrafo longo gerado para ocupar espaco de disco e memoria "
            "para testar o processamento massivo. O Atlas Cortex suportara isso?\n\n"
            "| Col 1 | Col 2 |\n"
            "|---|---|\n"
            f"| Data | [Link Interno](#{unique_word}) |\n\n"
        )
        parts.append(block)
        current_bytes += len(block)
        
    doc += "".join(parts)
    return doc

def run_stress_test(sizes_mb=[1, 5, 10, 25, 50, 100]):
    print("Iniciando Teste de Carga do Atlas Cortex...")
    print(f"Cargas alvo: {sizes_mb} MB")
    
    report = {}
    
    for size in sizes_mb:
        print(f"\n--- Preparando Chunk de ~{size} MB ---")
        
        start_gen = time.time()
        md_text = generate_synthetic_markdown(size)
        gen_time = time.time() - start_gen
        
        actual_size = len(md_text.encode('utf-8')) / (1024 * 1024)
        print(f"Tamanho gerado real: {actual_size:.2f} MB (Tempo de geracao: {gen_time:.2f}s)")
        
        print("Iniciando parsing pelo Engine...")
        start_parse = time.time()
        try:
            # Chama a função parse_text da SDK que invoca o subprocess
            result = parse_text(md_text, doc_id=f"stress_{size}mb")
            parse_time = time.time() - start_parse
            
            nodes_count = len(result.get("nodes", []))
            edges_count = len(result.get("edges", []))
            
            print(f"Sucesso! Tempo: {parse_time:.2f}s")
            print(f"Nodes gerados: {nodes_count} | Edges geradas: {edges_count}")
            
            report[f"{size}MB"] = {
                "status": "success",
                "actual_size_mb": actual_size,
                "parse_time_seconds": parse_time,
                "nodes_count": nodes_count,
                "edges_count": edges_count
            }
        except Exception as e:
            parse_time = time.time() - start_parse
            print(f"FALHA aos {parse_time:.2f}s: {e}")
            report[f"{size}MB"] = {
                "status": "failed",
                "actual_size_mb": actual_size,
                "time_before_fail": parse_time,
                "error": str(e)
            }
            # Se falhou, provavelmente por timeout ou OOM. Paramos o avanço para proteger o OS.
            print("Abortando próximas escalas para evitar crash.")
            break
            
        # Liberar memoria local forçado antes do proximo salto
        del md_text
        gc.collect()

    # Salva relatorio de telemetria
    report_file = Path("functional-probe") / "stress-report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))
    print(f"\nTelemetria salva em: {report_file}")
    
if __name__ == "__main__":
    run_stress_test([1, 5, 10, 25, 50, 100])
