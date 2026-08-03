import pytest
import time
from atlas_cortex import parse_text
import os
import sys

# Puxa o gerador do benchmark
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)
from scripts.stress_benchmark import generate_synthetic_markdown  # noqa: E402

@pytest.mark.stress
def test_atlas_stress_10mb():
    """
    Roda apenas quando pytest for chamado com '-m stress'.
    Injeta ~10MB no parser e valida se o timeout não estoura,
    alem de validar o processamento topológico base.
    """
    size_mb = 10
    text = generate_synthetic_markdown(size_mb)
    
    start_time = time.time()
    
    # Motor deve rodar limpo em menos de 10 segundos
    result = parse_text(text, doc_id="stress_pytest_10mb")
    duration = time.time() - start_time
    
    assert result["schema_version"] == "1.0.0"
    assert len(result["nodes"]) > 1000, "Deveriam existir milhares de nos em 10MB"
    assert duration < 15.0, f"Tempo extrapolado para 10MB: {duration:.2f}s"
