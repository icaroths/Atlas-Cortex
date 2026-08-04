# Atlas Cortex 🧠 — Enterprise Edition (100% Capacity)

**Motor de Parsing Semântico Determinístico para GraphRAG Corporativo (Edição Enterprise Irrestrita)**

![Version](https://img.shields.io/badge/version-2.0.0--enterprise-6d28d9?style=flat-square)
![Status](https://img.shields.io/badge/status-Production%20Ready-success?style=flat-square)
![Node Limit](https://img.shields.io/badge/node%20limit-Unrestricted-brightgreen?style=flat-square)
![Engine](https://img.shields.io/badge/engine-Rust%20PyO3%20%2B%20Tree--Sitter-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-73%2F73%20Passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-059669?style=flat-square)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=flat-square)

---

## 🔒 Repositório Privado Enterprise

Este é o **repositório oficial de desenvolvimento e produção Enterprise (`Atlas-Cortex_Dev`)**. 

Diferente do repositório público (que opera em modo de avaliação limitado a 750 nós), este ambiente privado oferece **100% de capacidade operacional do motor Rust**, permitindo o parsing semântico ilimitado de documentos massivos de qualquer extensão.

---

## 📐 Matemática & Benchmarks de Viabilidade

A viabilidade técnica e a eficiência operacional do Atlas Cortex V2 foram demonstradas matematicamente e validadas por experimentos empíricos executados nos scripts de benchmark do repositório:

### 1. Cálculo da Redução de Redundância por Zero-Overlap ($\Delta T$)

Em RAGs tradicionais (LangChain/LlamaIndex), documentos são fatiados com uma taxa de sobreposição (overlap) $\alpha \approx 15\%$ e duplicação de fronteiras de janela $\beta \approx 15\%$, gerando ~30% de redundância de tokens:
$$T_{\text{Tradicional}} = L \cdot (1 + \alpha + \beta) \approx 1.30 \cdot L$$

No Atlas Cortex, o parsing via AST Rust gera nós atômicos interconectados por grafos com zero sobreposição ($\alpha = 0, \beta = 0$):
$$T_{\text{Atlas}} = L \implies \Delta T = \frac{T_{\text{Tradicional}} - T_{\text{Atlas}}}{T_{\text{Tradicional}}} \approx 33.3\%$$

- **Economia de Armazenamento Vetorial**: **-38.42% de vetores no banco de dados**
- **Economia de Tokens em Ingestão/Chunking (Zero-Overlap)**: **~33.3% de economia média (25.41% a 37.77%)**
- **Economia de Custo de LLM (Retrieval Top-3)**: **-63.85% de tokens consumidos na janela de contexto (3.345 vs 9.254 tokens)**

### 2. Cálculo de Idempotência e Determinismo de Grafo (SHA-256)

Cada nó $N_k$ gera um ID imutável via hash criptográfico:
$$\text{ID}(N_k) = \text{SHA256}\Big(\text{DocID} \;\parallel\; \text{HeadingPath}(N_k) \;\parallel\; \text{Content}(N_k)\Big)$$

Invariância topológica garantida: $\text{Parse}(D) \equiv \text{Parse}(D)$, permitindo a reconciliação de grafos em tempo de execução $O(|\mathcal{V}| + |\mathcal{E}|)$, eliminando duplicações em bancos de grafos (Neo4j).

### 📊 Tabela de Resultados de Benchmarks Empíricos

| Métrica de Desempenho & Acurácia | RAG Tradicional (Fixed + Overlap) | Atlas Cortex V2 (Rust AST Graph) | Ganho / Melhoria |
| :--- | :--- | :--- | :--- |
| **Custo de Contexto no Retrieval (Top-3)** | 9,254 tokens | **3,345 tokens** | **-63.85% no consumo de LLM** |
| **Economia de Chunking (Zero-Overlap)** | Baseline (Sliding Window) | **Zero-Overlap AST** | **~33.3% de economia média** |
| **Espaço de Armazenamento Vetorial** | 24,180 tokens | **14,890 tokens** | **-38.42% no storage do Vector DB** |
| **Recall / Acurácia LLM-as-a-Judge** | 68.40% | **100.00% (15/15 aprovados)** | **+31.60% de acurácia** |
| **MRR (Mean Reciprocal Rank)** | 0.612 | **0.915** | **+49.5% na relevância** |
| **Integridade Estrutural de Tabelas** | 28.57% (corrompidas) | **100.00% (intactas)** | **+71.43% na fidelidade de dados** |
| **Velocidade de Parsing** | ~250ms / MB (Python) | **⚡ < 5ms / MB (Rust Engine)** | **> 50x mais rápido** |

> 📜 Para a formulação teórica e matemática completa, consulte [docs/MATEMATICA_E_BENCHMARKS.md](docs/MATEMATICA_E_BENCHMARKS.md).

---

## ⚡ Diferenciais da Edição Enterprise

| Recursos | Repositório Público (`Atlas-Cortex`) | Repositório Privado (`Atlas-Cortex_Dev`) |
| :--- | :--- | :--- |
| **Capacidade de Processamento** | ⚠️ Limite de 750 nós por documento | ♾️ **100% Irrestrito (Sem limites de nós)** |
| **Parsing AST em Rust** | ✅ Sim | ✅ Sim |
| **Desempenho de Carga** | Processamento básico | 🚀 **Suporte a estresse pesado (>100MB)** |
| **Preservação de Grafo** | Truncado acima de 750 nós | 🎯 **100% dos nós e arestas preservados** |
| **SDK Python & LangChain** | ✅ Sim | ✅ Sim |

---

## 📁 Arquitetura do Projeto Enterprise

```
Atlas-Cortex_Dev (v2.0.0-enterprise 100% Capacity)
│
├── engine/                          # Core em Rust (Sem trava de nós / 100% irrestrito)
│   ├── Cargo.toml                   # Dependências nativas
│   ├── deny.toml                    # Configuração do cargo-deny
│   └── src/main.rs                  # Core AST Parser ilimitado + 10 testes unitários Rust
│
├── python/                          # SDK & Camada de Integração
│   ├── atlas_cortex/                # parse_text(), parse_file(), reconcile_graphs()
│   └── tests/                       # 30 Testes de Integração & Estresse
│
├── docs/                            # Matemática, Papers, Benchmarks
│   ├── MATEMATICA_E_BENCHMARKS.md # Documento de matemática e teoremas
│   └── benchmarks/                  # Resultados empíricos JSON de eficiência e recall
│
├── scripts/                         # Ferramentas de Telemetria, Benchmark e SBOM
│   ├── generate_sbom.py             # Script de geração do SBOM CycloneDX
│   ├── stress_benchmark.py          # Benchmark de estresse (1MB a 100MB)
│   ├── benchmark_token_efficiency.py # Comparativo de economia de tokens
│   └── benchmark_retrieval_quality.py # Acurácia LLM-as-a-judge (100% accuracy)
│
├── CHANGELOG.md                     # Registro histórico de alterações
├── LIMITATIONS.md                   # Documentação das garantias Enterprise
├── SECURITY.md                      # Política de segurança
└── sbom-consolidated.json           # SBOM consolidado do projeto
```

---

## 🚀 Guia de Desenvolvimento

### 1. Compilando o Motor Enterprise
```bash
cd engine
cargo build --release
```

### 2. Testes Nativos em Rust (10/10)
```bash
cd engine && cargo test
```

### 3. Testes em Python (30/30) & Benchmark de Carga (100MB)
```bash
# Suíte padrão de testes
pytest python/tests --ignore=python/tests/test_stress.py

# Benchmark de estresse de carga pesada
python scripts/stress_benchmark.py
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `LICENSE` para mais detalhes.
