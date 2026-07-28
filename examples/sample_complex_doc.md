# 🧠 Atlas Cortex: Semantic Parsing Guide

Este documento serve como um exemplo intencionalmente projetado para falhar em estratégias clássicas de divisão de texto (como quebras baseadas em `chunk_size` fixo), mas brilhar através de parsers baseados em AST (Abstract Syntax Tree).

---

## 1. O Problema do RAG Clássico (LangChain)

No LangChain tradicional, usamos abordagens baseadas em tamanho e intersecção (overlap):

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
)
```

Isota garante que os trechos terão aproximadamente 1000 caracteres. Contudo, se este parágrafo ou o código acima for quebrado no meio, o LLM receptor não saberá a qual classe ou método ele pertence. A sobreposição (overlap) de 200 caracteres apenas introduz ruído em duplicidade (entropia).

---

## 2. A Solução do Atlas Cortex

O Atlas Cortex não olha para o texto como uma sequência linear de bytes. Ele olha para o texto como um **Grafo Estrutural (AST)**.

### 2.1 Parsers Nativos (Tree-sitter)
Graças ao uso do `tree-sitter-md`, sabemos exatamente onde um *heading* (título) começa, onde um parágrafo termina e quais blocos de código estão subordinados a qual subtítulo.

### 2.2 Tabela de Comparação de Desempenho

O impacto desta abordagem semântica é visível tanto em economia de tokens quanto em latência:

| Estratégia | Tokens Consumidos (P/ Query) | Latência Média | Recuperação Semântica |
|------------|------------------------------|----------------|-----------------------|
| Mecânica (1000/200) | 12,450 tokens | 1.8s | 68% |
| Atlas Cortex (AST) | 4,200 tokens | 0.6s | 89% |

Como mostrado na tabela, o Atlas Cortex mantém a estrutura íntegra enquanto corta o "lixo" invisível da borda de sobreposições, resultando em uma economia absurda nos limites de janela de contexto.
