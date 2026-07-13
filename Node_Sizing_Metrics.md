---
title: "Nota Técnica: Dimensionamento de Nós Semânticos (Node Sizing Metrics)"
author: "Icaro & Atlas (Aurelius OS)"
date: "Julho de 2026"
type: "technical-note"
---

# 📏 Dimensionamento de Nós Semânticos no Atlas Cortex

**Objetivo deste Documento:** Complementar o whitepaper principal (`Paper_Atlas_Cortex_PT.md`) respondendo a uma questão em aberto: **qual é, na prática, o tamanho de "1 nó" gerado pelo Roteador Topológico em Cascata?** Traduzimos essa medida em bytes e em quantidade de contexto de informação (tokens), permitindo comparação direta com *splitters* tradicionais baseados em contagem de tokens.

## 1. Por que o tamanho do nó não é uma constante

Diferente de sistemas de chunking clássico (ex: `RecursiveCharacterTextSplitter`, que fatia em blocos fixos de N tokens), o tamanho de um nó no Atlas Cortex é uma **variável dependente do Nível de Topologia** que o particionou:

| Nível | Critério de particionamento | Granularidade típica |
|---|---|---|
| **Nível 1 (Explícito)** | Headers Markdown, funções/classes (AST), tags DOM | Alta variância — depende da estrutura do autor original |
| **Nível 2 (Implícito)** | Quebras de parágrafo | Média — parágrafos técnicos em PT-BR |
| **Nível 3 (Densidade/Failsafe)** | Particionamento por volume fixo | Configurável — único nível com tamanho de nó constante por design |

## 2. Dados empíricos dos testes já reportados

Cruzando os *corpora* de teste com o número de nós gerados em cada bateria (dogfooding e NIAH, ver `Paper_Atlas_Cortex_PT.md`, Seção 4):

| Teste | Corpus (bytes) | Nós gerados | Bytes/nó (médio) |
|---|---|---|---|
| Corpus estruturado (whitepaper anterior) | ~2.097.152 | ~20.900 | **≈ 100 bytes/nó** |
| Dogfooding (fallback caótico, Nível 3) | ~2.097.152 | ~1.100–1.420 | **≈ 1.500–1.900 bytes/nó** |
| NIAH (Needle-in-a-Haystack) | ~1.855.979 | 2.003 | **≈ 926 bytes/nó** |

**Observação relevante:** o Nível 1 (estruturado) produz nós **~10–20× menores** que o fallback de densidade. Documentos bem formatados (Markdown com headers frequentes, funções curtas) geram granularidade fina naturalmente; texto caótico degrada para blocos maiores e mais grosseiros — um efeito colateral esperado do design do fallback, não uma inconsistência do sistema.

## 3. Tradução para tokens (unidade relevante para o LLM)

Para o modelo generativo, o que importa não é o byte, e sim o **token**. Usando a heurística padrão para tokenizadores BPE (~3,5–4 caracteres/token em português):

| Nível | Bytes/nó | Tokens/nó (estimado) | Equivalente prático |
|---|---|---|---|
| Nível 1 (típico) | ~100 bytes | **~25–30 tokens** | Cabeçalho ou assinatura de função com docstring curta |
| NIAH (parágrafo com contexto) | ~926 bytes | **~230–260 tokens** | Parágrafo técnico completo |
| Nível 3 (fallback) | ~1.500–1.900 bytes | **~400–480 tokens** | Próximo ao padrão de chunk clássico (256–512 tokens) |

## 4. Implicação para o Baseline Comparativo (Seção 5 do Whitepaper)

Esta tabela fornece a métrica que faltava para comparar, na mesma unidade, o Atlas Cortex contra *splitters* tradicionais: **tokens por chunk/nó**. O Nível 3 (failsafe) já opera na mesma faixa (256–512 tokens) usada por padrão em splitters como o do LangChain, o que sugere que a diferença arquitetural relevante está concentrada no Nível 1 — onde a granularidade é ditada pela semântica do documento, não por um limite arbitrário de tokens.

> **Nota de limitação:** os valores de tokens/nó acima são **estimativas heurísticas** (baseadas em razão caractere/token), não contagens diretas de um tokenizador real (ex: `tiktoken`, `cl100k_base`). Uma medição exata via tokenizador é recomendada como próximo passo antes de qualquer comparação formal de *overhead* com baselines (item já listado em Trabalhos Futuros do whitepaper principal).

---

## Referências

Ver `Paper_Atlas_Cortex_PT.md`, Seções 4 e 5, para a proveniência dos dados de teste (Dogfooding e NIAH) utilizados nesta nota.
