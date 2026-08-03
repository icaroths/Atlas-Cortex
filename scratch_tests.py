import json
from atlas_cortex import parse_text
import copy

def normalize(out):
    d = copy.deepcopy(out)
    d.pop("execution_id", None)
    d.pop("generated_at", None)
    d.pop("duration_ms", None)
    return d

print("=== TESTE A: Robustez de Âncoras ===")
text_a = "# Configuração & Setup\n\nVeja [detalhes](#configuração--setup).\n\n## Configuração & Setup\n"
print(json.dumps(parse_text(text_a), indent=2, ensure_ascii=False))

print("\n=== TESTE B: Idempotência ===")
text_b = "# A\n\n[B](#b)\n\n## B"
out1 = normalize(parse_text(text_b))
out2 = normalize(parse_text(text_b))
print("Idêntico?", out1 == out2)

print("\n=== TESTE C: Tabela com Link Interno ===")
text_c = "# Doc\n\n| Item | Ref |\n|---|---|\n| A | [B](#b) |\n\n## B\n"
print(json.dumps(parse_text(text_c), indent=2, ensure_ascii=False))
