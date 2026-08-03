# Atlas Cortex 🧠 — Evaluation Build (Public Repository)

**Motor de Parsing Semântico Determinístico para GraphRAG Corporativo (Versão de Avaliação)**

![Version](https://img.shields.io/badge/version-2.0.0--evaluation-6d28d9?style=flat-square)
![Build](https://img.shields.io/badge/build-Public%20Evaluation-f59e0b?style=flat-square)
![Node Limit](https://img.shields.io/badge/node%20limit-750-ef4444?style=flat-square)
![Engine](https://img.shields.io/badge/engine-Rust%20%2B%20Tree--Sitter-orange?style=flat-square)
![Tests](https://img.shields.io/badge/tests-40%2F40%20Passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-059669?style=flat-square)

> ⚠️ **Aviso Importante**: Este é o repositório público de avaliação do **Atlas Cortex**. Todas as compilações e branches deste repositório público possuem uma cota limite de **750 nós por documento**. Para obter acesso à versão **Enterprise com 100% de capacidade sem restrições**, entre em contato com os mantenedores ou acesse o repositório privado `Atlas-Cortex_Dev`.

---

## O que é o Atlas Cortex?

O **Atlas Cortex** é um motor de parsing semântico de alto desempenho escrito em **Rust**, projetado para transformar documentos Markdown em **grafos de conhecimento determinísticos (MOC - Map of Content)**, prontos para consumo por sistemas **GraphRAG** (*Graph-enhanced Retrieval-Augmented Generation*).

Ao invés de fatiar documentos de forma mecânica por contagem estática de tokens (como o `RecursiveCharacterTextSplitter` do LangChain), o Atlas utiliza a **Abstract Syntax Tree (AST)** do documento via **Tree-Sitter MD** em Rust para extrair nós semânticos **autocontidos e hierarquicamente interconectados**.

---

## ⚖️ Tabela Comparativa: Público (Evaluation) vs Privado (Enterprise)

| Recursos | Repositório Público (`Atlas-Cortex`) | Repositório Privado (`Atlas-Cortex_Dev`) |
| :--- | :--- | :--- |
| **Limite de Nós por Documento** | ⚠️ **Cota de 750 nós** | ♾️ **Ilimitado (100% da capacidade)** |
| **Parsing AST em Rust** | ✅ Sim | ✅ Sim |
| **Metadados de Truncamento** | ✅ Ativo (`"truncated": true`) | ℹ️ N/A (100% dos nós preservados) |
| **SDK Python & LangChain** | ✅ Sim | ✅ Sim |
| **Auditoria & SBOM** | ✅ Sim | ✅ Sim |
| **Suporte & Licenciamento** | ℹ️ Público / Avaliação | 🔒 Licença Enterprise Corporativa |

---

## 📁 Arquitetura do Projeto

```
Atlas-Cortex (Public Evaluation Build)
│
├── engine/                          # Motor Rust (Com trava de 750 nós para avaliação)
│   ├── Cargo.toml                   # Dependências nativas
│   ├── deny.toml                    # Configuração de auditoria de licenças
│   └── src/main.rs                  # Core AST Parser, trava de 750 nós + 10 testes Rust
│
├── python/                          # SDK Python & Integrações
│   ├── atlas_cortex/                # API: parse_text(), parse_file(), reconcile_graphs()
│   └── tests/                       # 30 Testes de Integração & Estresse
│
├── scripts/                         # Automações e SBOM
│   ├── generate_sbom.py             # Script de geração do SBOM CycloneDX
│   ├── stress_benchmark.py          # Benchmark de estresse
│   └── functional_probe.py          # Validador de integridade end-to-end
│
├── CHANGELOG.md                     # Histórico detalhado de evoluções
├── LIMITATIONS.md                   # Especificação da trava de 750 nós
├── SECURITY.md                      # Política de segurança
└── sbom-consolidated.json           # SBOM de dependências consolidado
```

---

## 🚀 Guia Rápido de Uso

### 1. Compilando o Motor

```bash
cd engine
cargo build --release
```

### 2. Uso com Python

```python
from atlas_cortex import parse_text

graph = parse_text("# Exemplo de Avaliação\nTestando o Atlas Cortex.")
print("Nós gerados:", len(graph["nodes"]))
print("Truncado:", graph.get("truncated", False))
```

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja `LICENSE` para mais informações.
