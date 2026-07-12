import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Activity, Zap, Shield, Database, ChevronRight, Cpu, Layers, GitMerge, FileText } from 'lucide-react';
import './index.css';

// Chart Data
const contextData = [
  { tokens: 0, AtlasCortex: 100, ClassicRAG: 100 },
  { tokens: 1000, AtlasCortex: 100, ClassicRAG: 92 },
  { tokens: 3000, AtlasCortex: 100, ClassicRAG: 75 },
  { tokens: 5000, AtlasCortex: 100, ClassicRAG: 45 },
  { tokens: 8000, AtlasCortex: 98, ClassicRAG: 15 },
  { tokens: 12000, AtlasCortex: 98, ClassicRAG: 5 },
];

// Translations Dictionary
const translations = {
  EN: {
    nav: { brand: 'Atlas Cortex', badge: 'AEGIS PROTOCOL ACTIVE' },
    hero: {
      title: 'The Semantic Integrity Engine for GenAI',
      subtitle: 'Eliminate context collapse in large-scale GraphRAG pipelines. Replace mechanical slicing with deterministic Topological Routing (MOC).',
      kpi1_title: 'Indexing Latency', kpi1_val: '0.003s', kpi1_sub: 'Linear O(N) | 1.77MB Corpus',
      kpi2_title: 'NIAH Retention', kpi2_val: '100%', kpi2_sub: 'Structural Chunk Integrity',
      kpi3_title: 'Search Complexity', kpi3_val: 'O(log V)', kpi3_sub: 'Direct Graph Retrieval'
    },
    problem: {
      tag: 'THE PROBLEM',
      title: 'Context Collapse & Signal Dilution',
      desc: 'Why do LLMs fail to retrieve information in massive documents?',
      text1: 'Traditional RAG architectures rely on algorithms like RecursiveCharacterTextSplitter. They blindly slice documents at arbitrary thresholds (e.g., 512 tokens), cutting sentences, code blocks, and context in half.',
      text2: 'When this fractured data is vectorized, the semantic signal is diluted. As the context window grows, the LLM suffers from a phenomenon analogous to "Barren Plateaus" in Quantum Machine Learning: the attention mechanism flattens, and the model hallucinates or ignores the data.',
      chart_title: 'Signal Retention vs Context Length',
      legend_atlas: 'Atlas Cortex (Atomic Routing)',
      legend_classic: 'Classic RAG (Blind Chunking)'
    },
    solution: {
      tag: 'THE SOLUTION',
      title: 'Atomic Semantic Routing',
      desc: 'The 5W framework explaining how Atlas Cortex solves the ingestion bottleneck.',
      tabs: {
        what: {
          label: 'WHAT',
          title: 'What is Atlas Cortex?',
          desc: 'An Enterprise RAG Preprocessing Engine. It maps document topology (Markdown, HTML, AST) into a Map of Content (MOC), parsing data by structural nodes rather than arbitrary token counts.',
          comp1: 'Classic RAG (LangChain)', comp1_desc: 'Splits text mechanically. Breaks logic.',
          comp2: 'Atlas Cortex', comp2_desc: 'Splits by hierarchy (H1, Section). Keeps 100% integrity.'
        },
        why: {
          label: 'WHY',
          title: 'Why was it built?',
          desc: 'To establish a strong architectural hypothesis: drastically reducing the noise inserted into the knowledge base. It is a highly effective structural preprocessing layer to prevent hallucinations.'
        },
        who: {
          label: 'WHO',
          title: 'Who is it for?',
          desc: 'Data Engineers, AI Architects, and Enterprise developers building large-scale pipelines that require absolute precision and cannot afford fractured context.'
        },
        when: {
          label: 'WHEN',
          title: 'When to use it?',
          desc: 'During the ingestion phase. Before vectorization, Atlas parses your PDFs, HTML, Code, and Markdown, generating a semantic graph instantly.'
        },
        where: {
          label: 'WHERE',
          title: 'Where does it run?',
          desc: 'Entirely In-Memory via the Aegis Protocol. It processes chaotic zip files and gigabytes of text without disk I/O bottlenecks, outputting clean structured JSON.'
        }
      }
    },
    evidence: {
      tag: 'EMPIRICAL EVIDENCE',
      title: 'Technical Proofs & Benchmarks',
      desc: 'Rigorous dogfooding and Needle-In-A-Haystack (NIAH) testing validating architectural resilience.',
      bench1: 'Corpus 1: Structured (Rules)',
      bench2: 'Corpus 2: Chaotic (Logs)',
      bench3: 'Needle-In-A-Haystack (NIAH)',
      bench3_desc: 'Processed 11,001 semantic blocks without IO lag. Extracted the needle perfectly anchored to its structural node, retaining 100% chunk integrity.'
    }
  },
  PT: {
    nav: { brand: 'Atlas Cortex', badge: 'PROTOCOLO AEGIS ATIVO' },
    hero: {
      title: 'O Motor de Integridade Semântica para GenAI',
      subtitle: 'Elimine o colapso de contexto em pipelines GraphRAG de larga escala. Substitua o fatiamento mecânico pelo Roteamento Topológico determinístico (MOC).',
      kpi1_title: 'Latência de Indexação', kpi1_val: '0.003s', kpi1_sub: 'Linear O(N) | Corpus 1.77MB',
      kpi2_title: 'Retenção NIAH', kpi2_val: '100%', kpi2_sub: 'Integridade Estrutural do Chunk',
      kpi3_title: 'Complexidade de Busca', kpi3_val: 'O(log V)', kpi3_sub: 'Recuperação Direta em Grafo'
    },
    problem: {
      tag: 'O PROBLEMA',
      title: 'Colapso de Contexto e Diluição de Sinal',
      desc: 'Por que os LLMs falham ao recuperar informações em documentos massivos?',
      text1: 'Arquiteturas RAG tradicionais dependem de algoritmos como RecursiveCharacterTextSplitter. Eles fatiam documentos cegamente em limites arbitrários (ex: 512 tokens), cortando frases, blocos de código e contexto pela metade.',
      text2: 'Quando esses dados fraturados são vetorizados, o sinal semântico é diluído. À medida que a janela de contexto cresce, o LLM sofre de um fenômeno análogo aos "Barren Plateaus" em QML: o mecanismo de atenção achata, e o modelo alucina.',
      chart_title: 'Retenção de Sinal vs Tamanho do Contexto',
      legend_atlas: 'Atlas Cortex (Roteamento Atômico)',
      legend_classic: 'RAG Clássico (Fatiamento Cego)'
    },
    solution: {
      tag: 'A SOLUÇÃO',
      title: 'Roteamento Semântico Atômico',
      desc: 'O framework 5W explicando como o Atlas Cortex resolve o gargalo de ingestão.',
      tabs: {
        what: {
          label: 'O QUE',
          title: 'O que é o Atlas Cortex?',
          desc: 'Um Motor de Pré-processamento RAG Corporativo. Ele mapeia a topologia (Markdown, HTML, AST) em um Grafo (MOC), extraindo dados por nós estruturais em vez de contagem arbitrária de tokens.',
          comp1: 'RAG Clássico (LangChain)', comp1_desc: 'Fatia texto mecanicamente. Quebra a lógica.',
          comp2: 'Atlas Cortex', comp2_desc: 'Fatia por hierarquia (H1, Seção). 100% de integridade.'
        },
        why: {
          label: 'POR QUE',
          title: 'Por que foi construído?',
          desc: 'Para estabelecer uma forte hipótese arquitetural: reduzir drasticamente o ruído inserido no banco de conhecimento. É uma camada de pré-processamento estrutural altamente eficaz para prevenir alucinações.'
        },
        who: {
          label: 'QUEM',
          title: 'Para quem é?',
          desc: 'Engenheiros de Dados, Arquitetos de IA e desenvolvedores Enterprise construindo pipelines que exigem precisão absoluta e não podem tolerar contexto fraturado.'
        },
        when: {
          label: 'QUANDO',
          title: 'Quando utilizar?',
          desc: 'Durante a fase de ingestão. Antes da vetorização, o Atlas analisa seus PDFs, HTML, Código e Markdown, gerando um grafo semântico instantaneamente.'
        },
        where: {
          label: 'ONDE',
          title: 'Onde ele roda?',
          desc: 'Totalmente em memória via Protocolo Aegis. Processa arquivos zip caóticos e gigabytes de texto sem gargalos de disco (I/O), gerando JSON estruturado.'
        }
      }
    },
    evidence: {
      tag: 'EVIDÊNCIA EMPÍRICA',
      title: 'Provas Técnicas e Benchmarks',
      desc: 'Testes rigorosos de dogfooding e Needle-In-A-Haystack (NIAH) validando a resiliência.',
      bench1: 'Corpus 1: Estruturado (Regras)',
      bench2: 'Corpus 2: Caótico (Logs)',
      bench3: 'Needle-In-A-Haystack (NIAH)',
      bench3_desc: 'Processou 11.001 blocos semânticos sem lag de IO. Extraiu a agulha perfeitamente ancorada ao seu nó estrutural, retendo 100% da integridade do chunk.'
    }
  }
};

const App = () => {
  const [lang, setLang] = useState<'EN' | 'PT'>('PT');
  const [activeTab, setActiveTab] = useState('what');
  
  const t = translations[lang];

  const getIcon = (key: string) => {
    switch(key) {
      case 'what': return <Database size={28} color="var(--neon-blue)" />;
      case 'why': return <Activity size={28} color="var(--neon-purple)" />;
      case 'who': return <Shield size={28} color="#10b981" />;
      case 'when': return <Zap size={28} color="#f59e0b" />;
      case 'where': return <Cpu size={28} color="#ec4899" />;
      default: return <FileText size={28} />;
    }
  };

  return (
    <>
      <div className="background-fx"></div>
      
      <nav className="navbar">
        <div className="nav-brand">{t.nav.brand}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div className="lang-toggle">
            <button className={`lang-btn ${lang === 'EN' ? 'active' : ''}`} onClick={() => setLang('EN')}>EN</button>
            <button className={`lang-btn ${lang === 'PT' ? 'active' : ''}`} onClick={() => setLang('PT')}>PT</button>
          </div>
        </div>
      </nav>

      <main className="container">
        {/* HERO SECTION */}
        <section className="hero">
          <h1>{t.hero.title}</h1>
          <p>{t.hero.subtitle}</p>
          
          <div className="kpi-grid glass-panel">
            <div className="kpi-card">
              <div className="kpi-title">{t.hero.kpi1_title}</div>
              <div className="kpi-value">{t.hero.kpi1_val}</div>
              <div className="kpi-subtext">{t.hero.kpi1_sub}</div>
            </div>
            <div className="kpi-card" style={{ borderLeft: '1px solid var(--glass-border)', borderRight: '1px solid var(--glass-border)' }}>
              <div className="kpi-title">{t.hero.kpi2_title}</div>
              <div className="kpi-value">{t.hero.kpi2_val}</div>
              <div className="kpi-subtext">{t.hero.kpi2_sub}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-title">{t.hero.kpi3_title}</div>
              <div className="kpi-value">{t.hero.kpi3_val}</div>
              <div className="kpi-subtext">{t.hero.kpi3_sub}</div>
            </div>
          </div>
        </section>

        {/* PROBLEM SECTION */}
        <section>
          <div className="section-header">
            <span className="section-tag">{t.problem.tag}</span>
            <h2 className="section-title">{t.problem.title}</h2>
            <p className="section-desc">{t.problem.desc}</p>
          </div>
          
          <div className="problem-grid">
            <div className="text-content glass-panel">
              <p>{t.problem.text1}</p>
              <p>{t.problem.text2}</p>
            </div>
            <div className="chart-content glass-panel">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', color: '#fff' }}>{t.problem.chart_title}</h3>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <AreaChart data={contextData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorAtlas" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--neon-blue)" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="var(--neon-blue)" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorClassic" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="tokens" stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 12}} />
                    <YAxis stroke="var(--text-muted)" tick={{fill: 'var(--text-muted)', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'rgba(10, 10, 12, 0.9)', border: '1px solid var(--neon-blue)', borderRadius: '8px' }}
                      itemStyle={{ color: 'var(--text-main)', fontWeight: 'bold' }}
                    />
                    <Legend verticalAlign="top" height={36} wrapperStyle={{ color: 'var(--text-muted)' }} />
                    <Area type="monotone" dataKey="AtlasCortex" stroke="var(--neon-blue)" strokeWidth={3} fillOpacity={1} fill="url(#colorAtlas)" name={t.problem.legend_atlas} />
                    <Area type="monotone" dataKey="ClassicRAG" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorClassic)" name={t.problem.legend_classic} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </section>

        {/* SOLUTION 5W SECTION */}
        <section>
          <div className="section-header">
            <span className="section-tag">{t.solution.tag}</span>
            <h2 className="section-title">{t.solution.title}</h2>
            <p className="section-desc">{t.solution.desc}</p>
          </div>

          <div className="five-w-container glass-panel">
            <div className="five-w-sidebar">
              {Object.keys(t.solution.tabs).map((key) => (
                <button 
                  key={key} 
                  className={`five-w-btn ${activeTab === key ? 'active' : ''}`}
                  onClick={() => setActiveTab(key)}
                >
                  <span style={{ textTransform: 'uppercase', letterSpacing: '1px' }}>{(t.solution.tabs as any)[key].label}</span>
                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
            
            <div className="five-w-content">
              <div className="content-header">
                {getIcon(activeTab)}
                <h2>{(t.solution.tabs as any)[activeTab].title}</h2>
              </div>
              <p>{(t.solution.tabs as any)[activeTab].desc}</p>
              
              {activeTab === 'what' && (
                <div className="comparison-box">
                  <div className="comp-item classic">
                    <h4>{t.solution.tabs.what.comp1}</h4>
                    <p>{t.solution.tabs.what.comp1_desc}</p>
                    <GitMerge size={40} style={{position: 'absolute', right: '1rem', top: '1rem', opacity: 0.1}} />
                  </div>
                  <div className="comp-item atlas">
                    <h4>{t.solution.tabs.what.comp2}</h4>
                    <p>{t.solution.tabs.what.comp2_desc}</p>
                    <Layers size={40} style={{position: 'absolute', right: '1rem', top: '1rem', opacity: 0.1}} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* EMPIRICAL EVIDENCE SECTION */}
        <section>
          <div className="section-header">
            <span className="section-tag">{t.evidence.tag}</span>
            <h2 className="section-title">{t.evidence.title}</h2>
            <p className="section-desc">{t.evidence.desc}</p>
          </div>

          <div className="benchmark-panel glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div className="benchmark-item">
              <div className="benchmark-item-header">
                <span className="benchmark-name">{t.evidence.bench1}</span>
                <span className="benchmark-time">0.015s</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '15%', background: '#f8fafc' }}></div>
              </div>
            </div>
            
            <div className="benchmark-item">
              <div className="benchmark-item-header">
                <span className="benchmark-name">{t.evidence.bench2}</span>
                <span className="benchmark-time">0.007s</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '7%', background: 'linear-gradient(90deg, #ec4899, #8a2be2)' }}></div>
              </div>
            </div>

            <div className="benchmark-item active-bench">
              <div className="benchmark-item-header">
                <span className="benchmark-name" style={{color: 'var(--neon-blue)'}}>{t.evidence.bench3}</span>
                <span className="benchmark-time">0.003s</span>
              </div>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '3%', background: 'linear-gradient(90deg, var(--neon-purple), var(--neon-blue))' }}></div>
              </div>
              <p className="bench-desc">{t.evidence.bench3_desc}</p>
            </div>
          </div>
        </section>
      </main>
      
      <footer>
        <p>© 2026 Atlas Cortex. Protocolo Aegis / Engenharia de Dados.</p>
      </footer>
    </>
  );
};

export default App;
