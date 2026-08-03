# Atlas Cortex 🧠 — Evaluation Build

**Motor de Parsing Semântico Determinístico para GraphRAG Corporativo**

![Version](https://img.shields.io/badge/version-2.0.0--evaluation-6d28d9?style=flat-square)
![Build](https://img.shields.io/badge/build-Evaluation-f59e0b?style=flat-square)
![Engine](https://img.shields.io/badge/engine-Rust%20%2B%20Tree--Sitter-orange?style=flat-square)
![Limit](https://img.shields.io/badge/node%20limit-750-ef4444?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-059669?style=flat-square)

> ⚠️ **Esta é a branch de avaliação.** O motor está funcional mas limitado a **750 nós por documento**. Para processamento sem restrições, consulte o branch [`main`](https://github.com/icaroths/Atlas-Cortex/tree/main) ou o repositório [Atlas-Cortex_Dev](https://github.com/icaroths/Atlas-Cortex_Dev) (privado).

---

## O que é o Atlas Cortex?

O **Atlas Cortex** é um motor de parsing semântico escrito em **Rust** que transforma documentos Markdown em **grafos de conhecimento determinísticos**, prontos para consumo por sistemas **GraphRAG** (*Graph-enhanced Retrieval-Augmented Generation*).

Ao invés de fatiar documentos por contagem de tokens (como o `RecursiveCharacterTextSplitter` do LangChain), o Atlas utiliza a **Abstract Syntax Tree (AST)** via Tree-Sitter para extrair nós semânticos **autocontidos e hierarquicamente conectados**.

**Resultado medido:** 63,85% de redução no consumo de tokens para o mesmo nível de recall.

---

## Limitações da Versão de Avaliação

| Característica | Evaluation | Enterprise |
|---|---|---|
| Nós por documento | **750** (truncado) | **Ilimitado** |
| Parser version | `2.0-eval` | `2.0` |
| Motor Rust (AST) | ✅ Completo | ✅ Completo |
| 3 tipos de aresta | ✅ | ✅ |
| Determinismo SHA-256 | ✅ | ✅ |
| Proteção OOM/DoS | ✅ | ✅ |
| LangChain Integration | ✅ | ✅ |
| Reconciliação de Grafos | ✅ | ✅ |
| Testes automatizados | ✅ 30 testes | ✅ 30 testes |
| Benchmarks de estresse | ❌ Limitado pela cota | ✅ Até 25MB |

> Para documentos com menos de 750 nós semânticos, a versão de avaliação produz **saída idêntica** à versão Enterprise.

---

## Início Rápido

### Pré-requisitos

- **Rust** 1.80+
- **Python** 3.9+

### Compilar o Engine

```bash
cd engine
cargo build --release
```

### Instalar o SDK Python

```bash
pip install -e .
```

### Uso Básico

```python
from atlas_cortex import parse_text, parse_file

result = parse_text("# Título\n\nParágrafo de conteúdo.", doc_id="meu_doc")
print(f"Nós: {len(result['nodes'])}")
print(f"Arestas: {len(result['edges'])}")
```

### Executar Testes

```bash
# Motor Rust
cd engine && cargo test --release

# Suite Python
pytest python/tests -v
```

---

## Estrutura de Saída (Schema v1.0.0)

```json
{
  "schema_version": "1.0.0",
  "parser_version": "2.0-eval",
  "doc_id": "meu_documento",
  "nodes": [
    {
      "id": "a3f2c1..._1",
      "type": "heading",
      "title": "Introdução",
      "content": "# Introdução",
      "raw_content": "# Introdução",
      "heading_path": [],
      "content_hash": "sha256..."
    }
  ],
  "edges": [
    {
      "id": "sha256...",
      "source": "a3f2c1..._2",
      "target": "a3f2c1..._1",
      "type": "child_of",
      "method": "heading_hierarchy"
    }
  ]
}
```

---

## Documentação Técnica

| Documento | Descrição |
|---|---|
| [Paper (PT)](docs/Paper_Atlas_Cortex_PT.md) | Artigo científico completo em Português |
| [Paper (EN)](docs/Paper_Atlas_Cortex_EN.md) | Main whitepaper in English |
| [GraphRAG Logic](docs/GRAPHRAG_LOGIC.md) | Como as arestas são construídas e o grafo navegado |
| [Quality Gate](docs/ATLAS_CORTEX_QUALITY_GATE.md) | Padrão de auditoria, segurança e entrega |

---

## Upgrade para Enterprise

Para remover a limitação de 750 nós e acessar o motor completo com benchmarks de estresse, reconciliação avançada e pipeline enterprise:

- **Branch `main`:** [github.com/icaroths/Atlas-Cortex](https://github.com/icaroths/Atlas-Cortex/tree/main) — código completo, público
- **Atlas-Cortex_Dev:** [github.com/icaroths/Atlas-Cortex_Dev](https://github.com/icaroths/Atlas-Cortex_Dev) — desenvolvimento sem restrições (privado)

---

*Construído com Rust, pragmatismo e rigor de engenharia. (c) 2026*
