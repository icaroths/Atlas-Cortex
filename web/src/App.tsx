import React, { useState } from 'react';
import { Upload, BrainCircuit, Activity } from 'lucide-react';
import { GraphVisualizer } from './components/GraphVisualizer';

function App() {
  const [graphData, setGraphData] = useState<any>(null);
  const [activeNode, setActiveNode] = useState<any>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const json = JSON.parse(event.target?.result as string);
          setGraphData(json);
          setActiveNode(null);
        } catch (error) {
          console.error("Invalid JSON file");
          alert("Por favor, selecione um arquivo .moc.json válido.");
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="relative w-screen h-screen">
      {/* Visualizador 3D no Background */}
      {graphData ? (
        <GraphVisualizer data={graphData} onNodeClick={setActiveNode} />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900 z-0">
          <BrainCircuit className="w-24 h-24 text-sky-500 opacity-20 mb-6" />
          <p className="text-slate-400 text-lg mb-4">Atlas Cortex - GraphRAG Visualizer</p>
          <label className="cursor-pointer glass-panel px-6 py-3 rounded-lg text-white hover:bg-slate-800/50 transition flex items-center gap-2">
            <Upload size={20} />
            <span>Carregar arquivo .moc.json</span>
            <input type="file" accept=".json" className="hidden" onChange={handleFileUpload} />
          </label>
        </div>
      )}

      {/* Painel Lateral Glassmorphism (Esquerda) */}
      <div className="absolute top-0 left-0 h-full w-80 glass-panel border-r p-6 flex flex-col z-10 pointer-events-none">
        <div className="flex items-center gap-3 mb-8 pointer-events-auto">
          <BrainCircuit className="w-8 h-8 text-sky-400" />
          <div>
            <h1 className="font-bold text-xl text-white tracking-tight">Atlas Cortex</h1>
            <p className="text-xs text-slate-400 font-medium tracking-wider uppercase">Visualizador 3D</p>
          </div>
        </div>

        {graphData && (
          <div className="mb-6 pointer-events-auto">
            <label className="cursor-pointer bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-400 text-sm px-4 py-2 rounded flex items-center justify-center gap-2 transition">
              <Upload size={16} />
              <span>Trocar Grafo</span>
              <input type="file" accept=".json" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>
        )}

        {graphData && (
          <div className="flex-1 overflow-y-auto pointer-events-auto pr-2 space-y-4">
            <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-slate-300 mb-2">
                <Activity size={16} className="text-emerald-400" />
                <span className="text-sm font-semibold">Métricas Topológicas</span>
              </div>
              <div className="text-3xl font-light text-white">{graphData.nodes?.length || 0}</div>
              <div className="text-xs text-slate-400 mt-1">Nós atômicos extraídos</div>
            </div>

            {activeNode && (
              <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-4 animate-in fade-in slide-in-from-left-4 duration-300">
                <div className="text-xs font-mono text-sky-400 mb-2">NODE_ID: {activeNode.id}</div>
                <h3 className="font-semibold text-white mb-2 leading-tight">{activeNode.title}</h3>
                <div className="text-sm text-slate-300 max-h-64 overflow-y-auto bg-slate-900/50 rounded p-3 border border-slate-800 font-mono whitespace-pre-wrap">
                  {activeNode.content}
                </div>
              </div>
            )}
            
            {!activeNode && graphData && (
              <div className="text-sm text-slate-400 text-center mt-12 opacity-50 animate-pulse">
                Clique em um nó espacial para inspecionar seu conteúdo
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
