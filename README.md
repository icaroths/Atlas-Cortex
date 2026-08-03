# Atlas Cortex 🧠 — Evaluation Edition

**Motor de Parsing Semântico Determinístico para GraphRAG Corporativo (Edição Pública de Avaliação)**

![Version](https://img.shields.io/badge/version-2.0.0--evaluation-6d28d9?style=flat-square)
![Build](https://img.shields.io/badge/build-Public%20Evaluation-f59e0b?style=flat-square)
![Node Limit](https://img.shields.io/badge/node%20limit-750-ef4444?style=flat-square)
![Engine](https://img.shields.io/badge/engine-Rust%20%2B%20Tree--Sitter-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-40%2F40%20Passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-059669?style=flat-square)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=flat-square)
![SBOM](https://img.shields.io/badge/SBOM-CycloneDX-informational?style=flat-square)

---

> ⚠️ **Aviso de Licenciamento & Cota Pública**: 
> Este é o **único repositório público oficial de avaliação do Atlas Cortex**. Todas as compilações deste repositório possuem uma cota limite de **750 nós por documento**. Se um documento exceder 750 nós, o grafo MOC será truncado de forma transparente com os metadados `"truncated": true`, `"original_node_count"` e `"truncated_node_count"`.
>
> 🔒 Para obter a versão **Enterprise sem restrições (100% da capacidade)**, consulte o repositório privado [`Atlas-Cortex_Dev`](https://github.com/icaroths/Atlas-Cortex_Dev).

---

## 📑 Sumário

- [O que é o Atlas Cortex?](#o-que-é-o-atlas-cortex)
- [Por que o Atlas Cortex existe?](#por-que-o-atlas-cortex-existe)
- [Tabela Comparativa: Evaluation vs Enterprise](#-tabela-comparativa-evaluation-vs-enterprise)
- [Arquitetura do Projeto & Governança](#-arquitetura-do-projeto--governança)
- [Guia Rápido de Uso](#-guia-rápido-de-uso)
- [Propriedades de Segurança & Limites](#-propriedades-de-segurança--limites)
- [Suíte de Testes & Qualidade](#-suíte-de-testes--qualidade)
- [Licença](#-licença)

---

## O que é o Atlas Cortex?

O **Atlas Cortex** é um motor de parsing semântico de alto desempenho escrito em **Rust**, projetado para transformar documentos Markdown em **grafos de conhecimento determinísticos (MOC - Map of Content)**, prontos para consumo por sistemas **GraphRAG** (*Graph-enhanced Retrieval-Augmented Generation*).

Ao invés de fatiar documentos de forma mecânica por contagem estática de tokens (como o `RecursiveCharacterTextSplitter` do LangChain, que frequentemente fragmenta frases, código e tabelas), o Atlas utiliza a **Abstract Syntax Tree (AST)** do documento via **Tree-Sitter MD** em Rust para extrair nós semânticos **autocontidos e hierarquicamente interconectados**.

---

## Por que o Atlas Cortex existe?

Sistemas RAG tradicionais sofrem de um problema estrutural:

```
Documento bruto
    ↓
Chunking por tamanho fixo (+ 10-20% overlap)
    ↓
Perda de hierarquia, tabelas fragmentadas, contexto perdido
    ↓
Retrieval fragmentado → LLM confuso → Alucinações
```

O Atlas Cortex propõe um caminho diferente:

```
Documento Markdown
    ↓
Parsing via AST (Tree-Sitter + Rust)
    ↓
Nós semânticos tipados (heading, paragraph, table, code_block)
    ↓
Grafo hierárquico com 3 tipos de aresta (child_of, references, semantically_related)
    ↓
Retrieval navegável e preciso → Contexto limpo → Respostas fiéis
```

**Resultado medido:** Economia comprovada de **63.85%** no consumo de tokens para o mesmo nível de recall semântico.

---

## ⚖️ Tabela Comparativa: Evaluation vs Enterprise

| Recursos & Capacidades | Repositório Público (`Atlas-Cortex`) | Repositório Privado (`Atlas-Cortex_Dev`) |
| :--- | :--- | :--- |
| **Limite de Nós por Documento** | ⚠️ **Cota de 750 nós** | ♾️ **Ilimitado (100% da capacidade)** |
| **Motor Rust AST** | ✅ Sim | ✅ Sim |
| **Metadados de Truncamento** | ✅ Ativo (`"truncated": true`) | ℹ️ N/A (100% dos nós preservados) |
| **Integridade de Tabelas JSON** | ✅ Sim | ✅ Sim |
| **IDs Determinísticos (SHA-256)** | ✅ Sim | ✅ Sim |
| **SDK Python & LangChain** | ✅ Sim | ✅ Sim |
| **Auditoria & SBOM CycloneDX** | ✅ Sim | ✅ Sim |
| **Suporte & Licenciamento** | ℹ️ Público / Avaliação (MIT) | 🔒 Licença Comercial Corporativa |

---

## 📁 Arquitetura do Projeto & Governança

```
Atlas-Cortex (v2.0.0-evaluation)
│
├── engine/                          # Motor Rust (Com cota de 750 nós para avaliação)
│   ├── Cargo.toml                   # Dependências nativas: tree-sitter-md, serde_json, sha2, anyhow
│   ├── deny.toml                    # Configuração de auditoria de licenças e vulnerabilidades
│   └── src/main.rs                  # Core AST Parser, trava de 750 nós + 10 testes unitários Rust
│
├── python/                          # SDK Python & Integrações
│   ├── atlas_cortex/
│   │   ├── __init__.py              # API principal: parse_text(), parse_file(), reconcile_graphs()
│   │   └── integrations/
│   │       └── langchain.py         # AtlasCortexSplitter para o ecossistema LangChain
│   └── tests/                       # 30 Testes de Integração & Estresse
│       ├── test_golden.py           # Testes golden de formato determinístico
│       ├── test_hostile.py          # Resiliência: null bytes, caótico e tabelas quebradas
│       ├── test_reconciliation.py   # Diff topológico de grafos (upsert incremental)
│       ├── test_schema.py           # Validação estrita de schema e tipos
│       ├── test_security.py         # Path traversal, symlink escape, timeouts, OOM
│       └── test_stress.py           # Benchmarks de carga pesada
│
├── scripts/                         # Automações, Benchmarks e SBOM
│   ├── generate_sbom.py             # Script de geração do SBOM CycloneDX
│   ├── functional_probe.py          # Validador de integridade end-to-end
│   ├── stress_benchmark.py          # Telemetria de escalabilidade (1MB → 100MB)
│   ├── benchmark_token_efficiency.py # Comparativo de economia de tokens
│   ├── mock_atlas_ingestor.py       # Ingestor atômico MOC
│   └── neo4j_graph_pipeline.py      # Pipeline de Ingestão para Neo4j
│
├── .github/workflows/               # CI/CD & Automação de Repositório
│   ├── ci.yml                       # Multi-stage CI (Cargo audit/fmt/clippy/test + Pytest/Ruff/Mypy)
│   └── auto-merge.yml               # Workflow autônomo de Pull Requests & Auto-Merge
│
├── CHANGELOG.md                     # Histórico detalhado de evoluções e lançamentos
├── LIMITATIONS.md                   # Especificação técnica da trava de 750 nós
├── SECURITY.md                      # Política de segurança e reporte de vulnerabilidades
├── sbom-consolidated.json           # Relatório SBOM de dependências consolidado
├── pyproject.toml                   # Configuração de empacotamento Python
└── requirements.txt                 # Dependências secundárias de benchmark
```

---

## 🚀 Guia Rápido de Uso

### 1. Compilando o Motor Rust

```bash
cd engine
cargo build --release
```
*O binário otimizado será gerado em `engine/target/release/engine`.*

### 2. Usando o SDK em Python

```python
from atlas_cortex import parse_text

markdown_doc = """
# Arquitetura do Sistema
O Atlas Cortex extrai grafos semânticos limpos.

## Benefícios
- Alta performance
- Zero alucinações
"""

graph = parse_text(markdown_doc)
print(f"Nós gerados: {len(graph['nodes'])}, Arestas: {len(graph['edges'])}")
print("Truncado:", graph.get("truncated", False))
```

### 3. Integração Nascida para LangChain

```python
from atlas_cortex.integrations.langchain import AtlasCortexSplitter

splitter = AtlasCortexSplitter()
documents = splitter.split_text(markdown_doc)

for doc in documents:
    print(f"Chunk ID: {doc.metadata['id']} | Título: {doc.metadata['title']}")
```

---

## 🛡️ Propriedades de Segurança & Limites

- **Auditoria de Licenças & Vulnerabilidades**: Verificado via `cargo audit`, `pip-audit`, `bandit` e `cargo-deny`.
- **Compliance SBOM**: Suporte nativo a geração de Bill of Materials via `python scripts/generate_sbom.py`.
- **Limites de Proteção**:
  - Cota Pública: **750 nós max por documento**.
  - Trava de tamanho máximo: **50 MB** (Prevenção de OOM).
  - Timeout por documento: **30 segundos**.
  - Profundidade máxima de AST: **100 níveis**.

Para detalhes técnicos completos sobre os limites, consulte [LIMITATIONS.md](LIMITATIONS.md).

---

## 📊 Suíte de Testes & Qualidade

```bash
# Executar suíte de testes unitários em Rust (10/10)
cd engine && cargo test

# Executar suíte de testes integrados em Python (30/30)
pytest python/tests --ignore=python/tests/test_stress.py
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `LICENSE` para mais informações.
