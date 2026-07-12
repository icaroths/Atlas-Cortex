# Atlas Cortex 🌐

**O Motor de Integridade Semântica para IA Generativa (GenAI)**

O **Atlas Cortex** é um motor de pré-processamento para sistemas corporativos GraphRAG. Ele foi construído para resolver o maior gargalo atual na ingestão de dados para LLMs: o **Colapso de Contexto** e a **Diluição de Sinal**. 

Ao invés de fatiar documentos de forma mecânica e cega por contagem de tokens (como o `RecursiveCharacterTextSplitter` do LangChain, que corta frases e blocos de código pela metade), o Atlas utiliza o **Roteamento Semântico Atômico**. Ele escaneia a topologia do documento (Markdown, HTML, AST de Códigos) e extrai os dados ancorados em nós estruturais, preservando 100% da integridade da informação e evitando alucinações (fenômeno análogo ao *Barren Plateaus* em Quantum Machine Learning).

---

## 📚 Documentação e Provas Técnicas

O arcabouço teórico e as provas de conceito empíricas encontram-se disponíveis na pasta `docs/`:

- 🇧🇷 [Artigo Científico Principal (Português)](docs/Paper_Atlas_Cortex_PT.md) - *Recomendado*
- 🇺🇸 [Main Whitepaper (English)](docs/Paper_Atlas_Cortex_EN.md)
- 📊 [Benchmark Empírico (Needle-In-A-Haystack e Dogfooding)](docs/QML_Ingestion_Proof.md)

---

## ⚡ Motor de Ingestão (Binário Fechado)

Para proteger a propriedade intelectual e o segredo industrial do Roteador em Cascata, o algoritmo original não está exposto. Disponibilizamos o motor compilado (`.exe`) via protocolo Aegis.

- **Local:** `bin/atlas-cortex-cli.exe`
- O binário é um executável portátil construído para ambientes Windows, capaz de varrer diretórios e arquivos zip caóticos puramente em memória (I/O livre de gargalos) e gerar o **MOC** (Map of Content) em formato de Grafo JSON a impressionantes **0.003s**.

---

## 🖥️ Dashboard Web Interativo (Frontend)

O repositório também inclui uma Landing Page construída em React/Vite com efeito *Glassmorphism* para ilustrar visualmente o problema do colapso de contexto e exibir os dados do *benchmark* (Suporte a PT-BR e EN).

Para rodar o painel interativo localmente:
```bash
cd web_dashboard
npm install
npm run dev
```
Acesse `http://localhost:5173` no seu navegador.

---
*Construído com pragmatismo para a Engenharia de Dados Corporativa. (c) 2026*
