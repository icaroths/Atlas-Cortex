# A Construção do Grafo Semântico (GraphRAG Logic)

O **Atlas Cortex** transcende o RAG tradicional (focado apenas em similaridade K-NN de fragmentos isolados) ao introduzir uma fundação nativa para **GraphRAG**. 

Enquanto a maioria dos sistemas de RAG extrai "nós atômicos" (os *vértices*), eles falham em manter as *arestas* (edges). Como resultado, o modelo perde a hierarquia do documento. O Atlas Cortex resolve isso no nível do parser AST (Abstract Syntax Tree).

## 1. Topologia Baseada em Hierarquia Estrita (Tree-sitter)

No Atlas Cortex, as arestas do Grafo de Conhecimento são formadas naturalmente pela estrutura linguística do documento processado, sem necessidade de inferência probabilística (LLMs).

### Regras de Arestas Nativas:

1. **Arestas de Paternidade (Parent-Child):**
   - Um heading de nível 2 (`##`) é automaticamente conectado ao heading de nível 1 (`#`) anterior.
   - Qualquer bloco de texto (Paragraph, List, Table) ou código (Fenced Code Block) é conectado bidirecionalmente ao heading mais recente que o escopa.
   
2. **Arestas de Sequência (Next-Sibling):**
   - Nós de mesmo nível sob o mesmo pai são conectados linearmente (ex: `H2_A -> H2_B`), preservando a ordem de leitura (chronological edges).

3. **Arestas de Referência Cruzada (Cross-Reference):**
   - Se um nó atômico contém links para outras seções do próprio documento (ex: `[veja a seção 2](#seção-2)`), o motor cria uma aresta explícita (`RELATES_TO`) mapeando o texto âncora para o nó alvo.

## 2. A Vantagem para o LLM

Ao passar o JSON estruturado (`.moc.json`) ou conectar essa saída diretamente a um banco Neo4j, o sistema de GraphRAG permite consultas complexas de multi-hop.

**Exemplo de Query:** *"Quais são os pré-requisitos para a configuração do servidor e qual script roda depois?"*
- **Vector RAG Clássico:** Pode recuperar o script, mas não o subtítulo "Pré-requisitos" se a semântica for sutil.
- **Atlas Cortex (GraphRAG):** Recupera o nó do "Script", sobe pela aresta `PARENT_OF` até "Configuração do Servidor", e desce na aresta `CHILD_OF` para os "Pré-requisitos", devolvendo o sub-grafo exato com 100% de precisão.

## 3. Próximos Passos (Enterprise)

Na versão Enterprise, além das arestas estáticas da AST, o Atlas Cortex injeta um pipeline de NLP/NER leve em Rust que:
- Extrai Entidades Nomeadas (Pessoas, Organizações, Tecnologias) durante o parsing.
- Cria arestas de co-ocorrência (`MENTIONS_ENTITY`) entre nós atômicos que falam sobre o mesmo conceito abstrato, unindo seções fisicamente distantes do documento.
