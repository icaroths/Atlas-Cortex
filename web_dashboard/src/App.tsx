import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, Cell } from 'recharts';
import { Activity, Zap, Shield, Database, ChevronRight, Cpu, Layers, GitMerge, FileText, TrendingUp, Mail } from 'lucide-react';
import './index.css';

// Chart Data — Signal Retention
const contextData = [
  { tokens: 0,     AtlasCortex: 100, ClassicRAG: 100 },
  { tokens: 1000,  AtlasCortex: 100, ClassicRAG: 92 },
  { tokens: 3000,  AtlasCortex: 100, ClassicRAG: 75 },
  { tokens: 5000,  AtlasCortex: 100, ClassicRAG: 45 },
  { tokens: 8000,  AtlasCortex: 98,  ClassicRAG: 15 },
  { tokens: 12000, AtlasCortex: 98,  ClassicRAG: 5  },
];

// Unleashed Throughput Data
const unleashhedData = [
  { label: 'Run 1 (cold)', nodes: 520679, time: 401.6, phi: 1296 },
  { label: 'Run 2 (delta)', nodes: 520679, time: 91.9,  phi: 5665 },
];

const translations = {
  EN: {
    nav: { brand: 'Atlas Cortex', badge: 'AEGIS PROTOCOL ACTIVE' },
    hero: {
      title: 'The Semantic Integrity Engine for GenAI',
      subtitle: 'Eliminate context collapse in large-scale GraphRAG pipelines. Replace mechanical slicing with deterministic Topological Routing (MOC).',
      kpi1_title: 'Indexing Latency',   kpi1_val: '0.003s',      kpi1_sub: 'Linear O(N) | 1.77MB Corpus',
      kpi2_title: 'NIAH Retention',     kpi2_val: '100%',         kpi2_sub: 'Structural Chunk Integrity',
      kpi3_title: 'Search Complexity',  kpi3_val: 'O(log V)',     kpi3_sub: 'Direct Graph Retrieval',
      kpi4_title: 'Delta Cache Hit',    kpi4_val: '99.8%',        kpi4_sub: 'Re-ingestion of unchanged files',
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
        what:  { label: 'WHAT',  title: 'What is Atlas Cortex?',  desc: 'An Enterprise RAG Preprocessing Engine. It maps document topology (Markdown, HTML, AST) into a Map of Content (MOC), parsing data by structural nodes rather than arbitrary token counts.',       comp1: 'Classic RAG (LangChain)', comp1_desc: 'Splits text mechanically. Breaks logic.', comp2: 'Atlas Cortex', comp2_desc: 'Splits by hierarchy (H1, Section). Keeps 100% integrity.' },
        why:   { label: 'WHY',   title: 'Why was it built?',      desc: 'To establish a strong architectural hypothesis: drastically reducing the noise inserted into the knowledge base. A highly effective structural preprocessing layer to prevent hallucinations in enterprise pipelines.' },
        who:   { label: 'WHO',   title: 'Who is it for?',         desc: 'Data Engineers, AI Architects, and Enterprise developers building large-scale pipelines that require absolute precision and cannot afford fractured context.' },
        when:  { label: 'WHEN',  title: 'When to use it?',        desc: 'During the ingestion phase. Before vectorization, Atlas parses your PDFs, HTML, Code, and Markdown, generating a clean semantic graph instantly — before a single token reaches the LLM.' },
        where: { label: 'WHERE', title: 'Where does it run?',     desc: 'Via the proprietary Aegis Protocol, Atlas Cortex operates with a fully decoupled I/O virtualization layer. It processes chaotic zip files and gigabytes of unstructured text, outputting clean, structured JSON without touching the host filesystem directly.' },
      }
    },
    evidence: {
      tag: 'EMPIRICAL EVIDENCE',
      title: 'Technical Proofs & Benchmarks',
      desc: 'Rigorous dogfooding and Needle-In-A-Haystack (NIAH) testing validating architectural resilience.',
      bench1: 'Corpus 1: Structured Rules',
      bench2: 'Corpus 2: Chaotic Logs (Fallback L3)',
      bench3: 'Needle-In-A-Haystack (NIAH)',
      bench3_desc: 'Processed 11,001 semantic blocks. Extracted the needle perfectly anchored to its structural node, retaining 100% chunk integrity.',
    },
    unleashed: {
      tag: 'STRESS TEST',
      title: 'Unleashed Mode: 520,679 Nodes',
      desc: 'Destructive benchmarking at full scale — 27,747 files from a multi-repository corpus.',
      cold: 'Cold Run (Full Ingestion)',
      warm: 'Warm Run (Delta Cache Active)',
      phi_label: 'Semantic Ingestion Rate (Φ)',
      phi_unit: 'nodes/s',
      files: 'Files Scanned',
      vertices: 'Semantic Vertices',
      entropy: 'Collision Entropy (Ec)',
      delta_rate: 'Delta Cache Reuse',
    },
    cta: {
      tag: 'ENTERPRISE LICENSE',
      title: 'Scale Beyond 750 Nodes',
      desc: 'The public binary is capped at 750 semantic nodes — built for proof-of-concept and research. For production-scale pipelines, Big Data workflows, or unlimited Aegis processing, contact us for an Enterprise License.',
      btn: 'Contact for Enterprise Access',
    }
  },
  PT: {
    nav: { brand: 'Atlas Cortex', badge: 'PROTOCOLO AEGIS ATIVO' },
    hero: {
      title: 'O Motor de Integridade Semântica para GenAI',
      subtitle: 'Elimine o colapso de contexto em pipelines GraphRAG de larga escala. Substitua o fatiamento mecânico pelo Roteamento Topológico determinístico (MOC).',
      kpi1_title: 'Latência de Indexação',  kpi1_val: '0.003s',   kpi1_sub: 'Linear O(N) | Corpus 1.77MB',
      kpi2_title: 'Retenção NIAH',          kpi2_val: '100%',      kpi2_sub: 'Integridade Estrutural do Chunk',
      kpi3_title: 'Complexidade de Busca',  kpi3_val: 'O(log V)', kpi3_sub: 'Recuperação Direta em Grafo',
      kpi4_title: 'Eficiência Delta Cache', kpi4_val: '99.8%',    kpi4_sub: 'Reuso em re-ingestão de corpus',
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
        what:  { label: 'O QUE',   title: 'O que é o Atlas Cortex?', desc: 'Um Motor de Pré-processamento RAG Corporativo. Ele mapeia a topologia (Markdown, HTML, AST) em um Grafo (MOC), extraindo dados por nós estruturais em vez de contagem arbitrária de tokens.',                           comp1: 'RAG Clássico (LangChain)', comp1_desc: 'Fatia texto mecanicamente. Quebra a lógica.', comp2: 'Atlas Cortex', comp2_desc: 'Fatia por hierarquia (H1, Seção). 100% de integridade.' },
        why:   { label: 'POR QUE', title: 'Por que foi construído?', desc: 'Para estabelecer uma forte hipótese arquitetural: reduzir drasticamente o ruído inserido no banco de conhecimento. É uma camada de pré-processamento estrutural altamente eficaz para prevenir alucinações em pipelines corporativos.' },
        who:   { label: 'QUEM',    title: 'Para quem é?',            desc: 'Engenheiros de Dados, Arquitetos de IA e desenvolvedores Enterprise construindo pipelines que exigem precisão absoluta e não podem tolerar contexto fraturado.' },
        when:  { label: 'QUANDO',  title: 'Quando utilizar?',        desc: 'Durante a fase de ingestão. Antes da vetorização, o Atlas analisa seus PDFs, HTML, Código e Markdown, gerando um grafo semântico limpo instantaneamente — antes que um único token chegue ao LLM.' },
        where: { label: 'ONDE',    title: 'Onde ele roda?',          desc: 'Via Protocolo Aegis proprietário, o Atlas Cortex opera com uma camada de virtualização de I/O totalmente desacoplada. Ele processa arquivos zip caóticos e gigabytes de texto não estruturado, produzindo JSON estruturado e limpo sem acessar diretamente o sistema de arquivos do host.' },
      }
    },
    evidence: {
      tag: 'EVIDÊNCIA EMPÍRICA',
      title: 'Provas Técnicas e Benchmarks',
      desc: 'Testes rigorosos de dogfooding e Needle-In-A-Haystack (NIAH) validando a resiliência arquitetural.',
      bench1: 'Corpus 1: Regras Estruturadas',
      bench2: 'Corpus 2: Logs Caóticos (Fallback L3)',
      bench3: 'Needle-In-A-Haystack (NIAH)',
      bench3_desc: 'Processou 11.001 blocos semânticos. Extraiu a agulha perfeitamente ancorada ao seu nó estrutural, retendo 100% da integridade do chunk.',
    },
    unleashed: {
      tag: 'STRESS TEST',
      title: 'Modo Unleashed: 520.679 Nós',
      desc: 'Benchmarking destrutivo em escala total — 27.747 arquivos de um corpus multi-repositório.',
      cold: 'Execução Fria (Ingestão Total)',
      warm: 'Execução Quente (Delta Cache Ativo)',
      phi_label: 'Taxa de Ingestão Semântica (Φ)',
      phi_unit: 'nós/s',
      files: 'Arquivos Varridos',
      vertices: 'Vértices Semânticos',
      entropy: 'Entropia de Colisão (Ec)',
      delta_rate: 'Reuso Delta Cache',
    },
    cta: {
      tag: 'LICENÇA ENTERPRISE',
      title: 'Escale Além de 750 Nós',
      desc: 'O binário público é limitado a 750 nós semânticos — projetado para provas de conceito e pesquisa. Para pipelines em produção, workflows de Big Data ou processamento Aegis ilimitado, entre em contato para uma Licença Enterprise.',
      btn: 'Contato para Acesso Enterprise',
    }
  }
};

// Scroll Reveal Hook
function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.15 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return { ref, visible };
}

const RevealSection: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => {
  const { ref, visible } = useScrollReveal();
  return (
    <div ref={ref} className={`reveal-section ${visible ? 'revealed' : ''} ${className ?? ''}`}>
      {children}
    </div>
  );
};

const App = () => {
  const [lang, setLang] = useState<'EN' | 'PT'>('PT');
  const [activeTab, setActiveTab] = useState('what');
  const t = translations[lang];

  const getIcon = (key: string) => {
    switch(key) {
      case 'what':  return <Database size={28} color="var(--neon-blue)" />;
      case 'why':   return <Activity size={28} color="var(--neon-purple)" />;
      case 'who':   return <Shield size={28} color="#10b981" />;
      case 'when':  return <Zap size={28} color="#f59e0b" />;
      case 'where': return <Cpu size={28} color="#ec4899" />;
      default:      return <FileText size={28} />;
    }
  };

  // Benchmark speed display: higher speed = wider bar
  const benchmarks = [
    { name: t.evidence.bench1, time: '0.015s', speed: 67,  color: '#f8fafc' },
    { name: t.evidence.bench2, time: '0.007s', speed: 100, color: 'linear-gradient(90deg, #ec4899, #8a2be2)' },
    { name: t.evidence.bench3, time: '0.003s', speed: 100, color: 'linear-gradient(90deg, var(--neon-purple), var(--neon-blue))', active: true, desc: t.evidence.bench3_desc },
  ];

  return (
    <>
      <div className="background-fx"></div>

      {/* NAV */}
      <nav className="navbar">
        <div className="nav-brand">{t.nav.brand}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <span className="aegis-badge">{t.nav.badge}</span>
          <div className="lang-toggle">
            <button className={`lang-btn ${lang === 'EN' ? 'active' : ''}`} onClick={() => setLang('EN')}>EN</button>
            <button className={`lang-btn ${lang === 'PT' ? 'active' : ''}`} onClick={() => setLang('PT')}>PT</button>
          </div>
        </div>
      </nav>

      <main className="container">
        {/* HERO */}
        <section className="hero">
          <div className="hero-tag">⚡ AEGIS PROTOCOL</div>
          <h1>{t.hero.title}</h1>
          <p>{t.hero.subtitle}</p>
          <div className="kpi-grid glass-panel">
            {[
              { title: t.hero.kpi1_title, val: t.hero.kpi1_val, sub: t.hero.kpi1_sub, color: 'var(--neon-blue)' },
              { title: t.hero.kpi2_title, val: t.hero.kpi2_val, sub: t.hero.kpi2_sub, color: '#10b981' },
              { title: t.hero.kpi3_title, val: t.hero.kpi3_val, sub: t.hero.kpi3_sub, color: 'var(--neon-purple)' },
              { title: t.hero.kpi4_title, val: t.hero.kpi4_val, sub: t.hero.kpi4_sub, color: '#f59e0b' },
            ].map((kpi, i) => (
              <div key={i} className="kpi-card" style={{ borderLeft: i > 0 ? '1px solid var(--glass-border)' : undefined }}>
                <div className="kpi-title">{kpi.title}</div>
                <div className="kpi-value" style={{ color: kpi.color }}>{kpi.val}</div>
                <div className="kpi-subtext">{kpi.sub}</div>
              </div>
            ))}
          </div>
        </section>

        {/* PROBLEM */}
        <RevealSection>
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
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(10,10,12,0.9)', border: '1px solid var(--neon-blue)', borderRadius: '8px' }} itemStyle={{ color: 'var(--text-main)', fontWeight: 'bold' }} />
                      <Legend verticalAlign="top" height={36} wrapperStyle={{ color: 'var(--text-muted)' }} />
                      <Area type="monotone" dataKey="AtlasCortex" stroke="var(--neon-blue)" strokeWidth={3} fillOpacity={1} fill="url(#colorAtlas)" name={t.problem.legend_atlas} />
                      <Area type="monotone" dataKey="ClassicRAG"  stroke="#ef4444"           strokeWidth={3} fillOpacity={1} fill="url(#colorClassic)" name={t.problem.legend_classic} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </section>
        </RevealSection>

        {/* SOLUTION 5W */}
        <RevealSection>
          <section>
            <div className="section-header">
              <span className="section-tag">{t.solution.tag}</span>
              <h2 className="section-title">{t.solution.title}</h2>
              <p className="section-desc">{t.solution.desc}</p>
            </div>
            <div className="five-w-container glass-panel">
              <div className="five-w-sidebar">
                {Object.keys(t.solution.tabs).map((key) => (
                  <button key={key} className={`five-w-btn ${activeTab === key ? 'active' : ''}`} onClick={() => setActiveTab(key)}>
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
        </RevealSection>

        {/* EMPIRICAL EVIDENCE */}
        <RevealSection>
          <section>
            <div className="section-header">
              <span className="section-tag">{t.evidence.tag}</span>
              <h2 className="section-title">{t.evidence.title}</h2>
              <p className="section-desc">{t.evidence.desc}</p>
            </div>
            <div className="benchmark-panel glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
              {benchmarks.map((b, i) => (
                <div key={i} className={`benchmark-item ${b.active ? 'active-bench' : ''}`}>
                  <div className="benchmark-item-header">
                    <span className="benchmark-name" style={b.active ? { color: 'var(--neon-blue)' } : {}}>{b.name}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span className="speed-label">SPEED</span>
                      <span className="benchmark-time">{b.time}</span>
                    </div>
                  </div>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${b.speed}%`, background: b.color }}></div>
                  </div>
                  <div className="speed-note">{b.speed === 100 ? '⚡ Fastest' : `${b.speed}% relative speed`}</div>
                  {b.desc && <p className="bench-desc">{b.desc}</p>}
                </div>
              ))}
            </div>
          </section>
        </RevealSection>

        {/* UNLEASHED STRESS TEST */}
        <RevealSection>
          <section>
            <div className="section-header">
              <span className="section-tag">{t.unleashed.tag}</span>
              <h2 className="section-title">{t.unleashed.title}</h2>
              <p className="section-desc">{t.unleashed.desc}</p>
            </div>
            <div className="unleashed-grid">
              {/* Stat Cards */}
              <div className="unleashed-stats glass-panel">
                {[
                  { label: t.unleashed.files,     val: '27,747',   icon: <FileText size={20} color="var(--neon-blue)" /> },
                  { label: t.unleashed.vertices,   val: '520,679',  icon: <Layers   size={20} color="var(--neon-purple)" /> },
                  { label: t.unleashed.entropy,    val: '≈ 0',      icon: <Shield   size={20} color="#10b981" /> },
                  { label: t.unleashed.delta_rate, val: '99.8%',    icon: <TrendingUp size={20} color="#f59e0b" /> },
                ].map((s, i) => (
                  <div key={i} className="stat-card">
                    <div className="stat-icon">{s.icon}</div>
                    <div className="stat-val">{s.val}</div>
                    <div className="stat-label">{s.label}</div>
                  </div>
                ))}
              </div>
              {/* Phi Chart */}
              <div className="phi-chart glass-panel">
                <h3 style={{ marginBottom: '0.5rem', color: '#fff' }}>{t.unleashed.phi_label}</h3>
                <div style={{ width: '100%', height: 240 }}>
                  <ResponsiveContainer>
                    <BarChart data={unleashhedData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="label" stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <YAxis stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <Tooltip
                        formatter={(v: number) => [`${v.toLocaleString()} ${t.unleashed.phi_unit}`, 'Φ']}
                        contentStyle={{ backgroundColor: 'rgba(10,10,12,0.9)', border: '1px solid var(--neon-purple)', borderRadius: '8px' }}
                        itemStyle={{ color: 'var(--neon-blue)', fontWeight: 'bold' }}
                      />
                      <Bar dataKey="phi" radius={[6, 6, 0, 0]}>
                        <Cell fill="#4a1d96" />
                        <Cell fill="url(#phiGradient)" />
                        <defs>
                          <linearGradient id="phiGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="var(--neon-blue)" />
                            <stop offset="100%" stopColor="var(--neon-purple)" />
                          </linearGradient>
                        </defs>
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                  Φ Cold: 1,296 nodes/s → Φ Delta: <strong style={{ color: 'var(--neon-blue)' }}>5,665 nodes/s</strong>
                </p>
              </div>
            </div>
          </section>
        </RevealSection>

        {/* CTA ENTERPRISE */}
        <RevealSection>
          <section className="cta-section">
            <div className="cta-panel glass-panel">
              <span className="section-tag">{t.cta.tag}</span>
              <h2 className="section-title" style={{ marginTop: '1rem' }}>{t.cta.title}</h2>
              <p className="section-desc" style={{ marginBottom: '2.5rem' }}>{t.cta.desc}</p>
              <a href="mailto:atlas.enterprise@example.com" className="cta-btn">
                <Mail size={18} />
                {t.cta.btn}
              </a>
            </div>
          </section>
        </RevealSection>
      </main>

      <footer>
        <p>© 2026 Atlas Cortex · Aegis Protocol · Data Engineering</p>
      </footer>
    </>
  );
};

export default App;
