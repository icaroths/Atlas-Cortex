# Atlas Cortex 🧠 — Evaluation Edition

**Motor de Parsing Semântico Determinístico para GraphRAG Corporativo (Edição de Avaliação)**

![Version](https://img.shields.io/badge/version-2.0.0--evaluation-6d28d9?style=flat-square)
![Build](https://img.shields.io/badge/build-Evaluation%20Quota-f59e0b?style=flat-square)
![Limit](https://img.shields.io/badge/node%20limit-750-ef4444?style=flat-square)
![Engine](https://img.shields.io/badge/engine-Rust%20%2B%20Tree--Sitter-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-40%2F40%20Passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-059669?style=flat-square)

> ⚠️ **Esta é a branch de avaliação.** Esta versão possui uma cota limite de **750 nós por documento**. Se o documento exceder 750 nós, o grafo MOC será truncado de forma transparente com as flags `"truncated": true`, `"original_node_count"` e `"truncated_node_count"`. Para a versão sem restrições, consulte a branch [`main`](https://github.com/icaroths/Atlas-Cortex/tree/main).

---

## ⚖️ Comparativo: Evaluation vs Enterprise

| Recursos | Evaluation Edition (Esta Branch) | Enterprise Edition (`main`) |
| :--- | :--- | :--- |
| **Limite de Nós por Documento** | ⚠️ Max 750 nós | ♾️ Sem limites |
| **Motor Rust AST** | ✅ Sim | ✅ Sim |
| **Integridade de Tabelas JSON** | ✅ Sim | ✅ Sim |
| **Metadados de Truncamento** | ✅ Ativo (`"truncated": true`) | ℹ️ N/A (não é truncado) |
| **SDK Python & LangChain** | ✅ Sim | ✅ Sim |
| **Suporte & SLAs** | ℹ️ Comunidade | 🛡️ Garantia Enterprise |

---

## 📁 Arquitetura do Projeto

```
Atlas-Cortex (v2.0.0-evaluation)
│
├── engine/                          # Motor de Altíssima Performance (Rust)
│   ├── Cargo.toml                   # Dependências nativas
│   ├── deny.toml                    # Auditoria de licenças
│   └── src/main.rs                  # Core AST Parser com trava de 750 nós + 10 testes Rust
│
├── python/                          # SDK Python & Integrações
│   ├── atlas_cortex/                # parse_text(), parse_file(), reconcile_graphs()
│   └── tests/                       # 30 Testes de Integração
│
├── scripts/                         # Automações e SBOM
│   ├── generate_sbom.py             # Script de geração do SBOM CycloneDX
│   ├── stress_benchmark.py          # Benchmark de estresse
│   └── functional_probe.py          # Probe de diagnóstico
│
├── CHANGELOG.md                     # Histórico detalhado de evoluções
├── LIMITATIONS.md                   # Documentação detalhada dos limites de 750 nós
├── SECURITY.md                      # Política de segurança
└── sbom-consolidated.json           # SBOM consolidado
```

---

## 🚀 Como Testar a Edição de Avaliação

### 1. Compilando a Engine
```bash
cd engine
cargo build --release
```

### 2. Testando via SDK Python
```python
from atlas_cortex import parse_text

# Textos pequenos (< 750 nós) serão processados normalmente.
# Textos muito extensos terão a flag 'truncated': True no grafo resultante.
graph = parse_text("# Teste\nDocumento de avaliação.")
print("Truncado:", graph.get("truncated", False))
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `LICENSE` para mais informações.
