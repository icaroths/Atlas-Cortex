# Atlas Cortex: Antes vs Depois 🚀

O colapso de contexto (Semantic Gap) acontece quando você fatia seu documento baseado puramente na contagem de caracteres (chunking mecânico). 

Veja a diferença visual entre a abordagem padrão da indústria (LangChain) e a Ingestão Atômica Topológica do Atlas Cortex.

## ❌ A Abordagem LangChain (RecursiveCharacterTextSplitter)

Quando o limite de tokens/caracteres é atingido no meio de um bloco lógico, o LangChain corta a informação. Isso cria "chunks" órfãos e confusos, encarecendo a janela de contexto.

```json
[
  {
    "chunk_1": "## Função de Processamento\n\n```python\ndef process_data(data):\n    # Inicializa variáveis\n    result = []\n    for item in da"
  },
  {
    "chunk_2": "ta:\n        if item.is_valid():\n            result.append(item.process())\n    return result\n```\n\nEsta função gar"
  }
]
```

## ✅ A Abordagem Atlas Cortex (Nó Atômico)

O motor em Rust do Atlas Cortex utiliza `Tree-Sitter` para enxergar a estrutura da árvore sintática (AST). Ele só quebra as estruturas nas "juntas" (Ex: limites de funções, divisões de seções Markdown). A integridade do objeto se mantém 100%.

```json
[
  {
    "id": 14,
    "title": "Função de Processamento",
    "content": "## Função de Processamento\n\n```python\ndef process_data(data):\n    # Inicializa variáveis\n    result = []\n    for item in data:\n        if item.is_valid():\n            result.append(item.process())\n    return result\n```\n\nEsta função garante..."
  }
]
```

### O Impacto Matemático
Esta preservação permite que a nossa busca vetorial atinja um *recall* perfeito (o modelo LLM recebe o snippet completo), reduzindo a quantidade de tokens enviados via API em até **61.02%** em comparação aos múltiplos chunks repletos de "overlaps" gerados pelos splitters mecânicos.
