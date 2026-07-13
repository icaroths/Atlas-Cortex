# Atlas Cortex 🌐

**Motor de Pré-processamento Estrutural para RAG Corporativo**

![Version](https://img.shields.io/badge/version-1.0.0--stable-6d28d9?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2064--bit-0ea5e9?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/license-Freemium%20%2F%20Enterprise-059669?style=flat-square)
![Nodes](https://img.shields.io/badge/public%20cap-750%20nodes-f59e0b?style=flat-square)

O **Atlas Cortex** é um motor de pré-processamento para sistemas corporativos GraphRAG. Ele foi construído para mitigar um dos gargalos centrais na ingestão de dados para LLMs: o **Colapso de Contexto** e a **Diluição de Sinal**, causados pela fragmentação mecânica de documentos longos.

Ao invés de fatiar documentos de forma cega por contagem de tokens (como o `RecursiveCharacterTextSplitter` do LangChain, que pode cortar frases e blocos de código pela metade), o Atlas utiliza o **Roteamento Semântico Atômico**: ele escaneia a topologia do documento (headers Markdown, tags HTML, AST de código) e particiona os dados ancorados em nós estruturais.

> **O que já foi validado empiricamente:** o roteamento preserva a integridade *estrutural* dos chunks (nós não são cortados no meio de uma seção ou função) e evita falhas de indexação (OOM) mesmo em corpora caóticos, via *fallback* gracioso.
> **O que ainda não foi medido:** o impacto disso na taxa de alucinação ou na precisão/recall do *retrieval* final do LLM — essas métricas exigem benchmarks end-to-end (ex: RAGAS, MS MARCO/BEIR) ainda não executados. Ver limitações detalhadas na documentação abaixo.

---

## 📚 Documentação e Provas Técnicas

O arcabouço teórico e as provas de conceito empíricas encontram-se disponíveis na pasta `docs/`:

- 🇧🇷 [Artigo Científico Principal (Português)](docs/Paper_Atlas_Cortex_PT.md) - *Recomendado*
- 🇺🇸 [Main Whitepaper (English)](docs/Paper_Atlas_Cortex_EN.md)
- 📊 [Benchmark Empírico (Needle-In-A-Haystack e Dogfooding)](docs/QML_Ingestion_Proof.md)
- 📏 [Nota Técnica: Dimensionamento de Nós (bytes/tokens)](docs/Node_Sizing_Metrics.md)

Todos os documentos acima incluem, explicitamente, as limitações metodológicas de cada teste — recomendamos a leitura da seção "Discussão e Limitações" do artigo principal antes de qualquer avaliação de adoção.

---

## ⚡ Motor de Ingestão (Binário Fechado)

Para proteger a propriedade intelectual do Roteador em Cascata, o algoritmo original não está exposto neste repositório. Disponibilizamos o motor compilado (`.exe`) via protocolo Aegis.

- **Local:** `bin/atlas-cortex-cli.exe`
- O binário é um executável portátil construído para ambientes Windows, capaz de varrer diretórios e arquivos zip caóticos puramente em memória, gerando o **MOC** (Map of Content) em formato de Grafo JSON.

### 💻 Requisitos de Sistema

| Requisito | Especificação |
|---|---|
| Sistema Operacional | Windows 10 / 11 (64-bit) |
| Arquitetura | x86_64 |
| RAM Mínima | 512 MB livres |
| Dependências | Nenhuma — executável autocontido |
| VC++ Redistributable | Não necessário (embutido) |

### 💻 Como Usar o Executável?

A ferramenta é um utilitário de linha de comando (CLI) *plug-and-play*. Não é necessário instalar Python, bibliotecas ou dependências.

Abra o **PowerShell** ou o **Prompt de Comando (CMD)** na pasta onde o executável se encontra e rode os comandos abaixo.

**1. Ver a ajuda e comandos disponíveis:**
```powershell
.\bin\atlas-cortex-cli.exe --help
```

**2. Ingerir e indexar todos os arquivos Markdown de uma pasta específica:**
```powershell
.\bin\atlas-cortex-cli.exe ingest --path "C:\Caminho\Para\Seus\Documentos" --type md
```

**3. Testar o Benchmark do Roteador (Needle-In-A-Haystack):**
```powershell
.\bin\atlas-cortex-cli.exe niah
```

O Atlas vai varrer a pasta, respeitar as barreiras estruturais do seu texto e devolver o índice (Map of Content) particionado por nó semântico.

---

## 🖥️ Dashboard Web Interativo (Frontend)

O repositório também inclui uma landing page construída em React/Vite para ilustrar visualmente o problema do colapso de contexto e exibir os dados do benchmark (suporte a PT-BR e EN).

Para rodar o painel interativo localmente:
```bash
cd web_dashboard
npm install
npm run dev
```
Acesse `http://localhost:5173` no seu navegador.

---

## 🏷️ Modelo Comercial (Licenciamento & Cotas)

> Esta seção descreve o **produto** distribuído neste repositório (o binário `.exe`) — condições de uso, cotas e planos. Ela é independente das seções de pesquisa/documentação acima: os números aqui refletem política comercial, não resultados de benchmark publicados.

### Freemium (Safe Mode)

O binário distribuído neste repositório permite o processamento gratuito de até **750 Nós Semânticos**, restrito a **3 execuções diárias**. Essa cota é dimensionada para provas de conceito, automação pessoal e testes laboratoriais (equivalente a repositórios de código médios ou alguns livros curtos). O sistema contabiliza nós e acessos diários, e trava a execução localmente via ancoragem de hardware (*Hardware Lock*).

Ao atingir o limite (nós ou execuções diárias), a ferramenta exibirá um aviso.

### Enterprise (Sem Limites)

Para uso corporativo em larga escala ou pipelines de Big Data, é necessária a aquisição da licença Enterprise. O plano Enterprise remove os limites de nós e execuções diárias do Safe Mode.

**Nota de transparência:** as cifras de vazão divulgadas para o plano Enterprise (nós/segundo em escala de centenas de milhares) referem-se a ensaios internos, executados em ambiente próprio, sem metodologia ou corpus publicados neste repositório — portanto, não devem ser lidas como benchmark reproduzível ou comparável aos testes documentados em `docs/`. Uma publicação formal desses números, com metodologia e corpus descritos, está nos planos de trabalhos futuros.

Para aquisição de licença, suporte ou relato de problemas, contate: **icaro.thares@gmail.com**.

---
*Construído com pragmatismo para a Engenharia de Dados Corporativa. (c) 2026*
