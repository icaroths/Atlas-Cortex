import React, { useRef, useMemo, useState, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

interface MocNode {
  id: number;
  title: string;
  content: string;
}

interface GraphVisualizerProps {
  data: { nodes: MocNode[] };
  onNodeClick: (node: MocNode) => void;
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ data, onNodeClick }) => {
  const fgRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight });

  // Escuta redimensionamento da janela
  useEffect(() => {
    const handleResize = () => setDimensions({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const graphData = useMemo(() => {
    const nodes = data.nodes.map(n => ({ ...n, val: 1 }));
    const links: any[] = [];
    
    // Constrói links baseados na hierarquia markdown (h1, h2, h3)
    let lastH1: any = null;
    let lastH2: any = null;

    nodes.forEach(node => {
      const isH1 = node.title.startsWith('# ');
      const isH2 = node.title.startsWith('## ');
      const isH3 = node.title.startsWith('### ');

      if (isH1) {
        lastH1 = node;
        lastH2 = null;
        node.val = 3; // Tamanho maior
      } else if (isH2) {
        lastH2 = node;
        node.val = 2;
        if (lastH1) links.push({ source: lastH1.id, target: node.id });
      } else if (isH3) {
        node.val = 1;
        if (lastH2) links.push({ source: lastH2.id, target: node.id });
        else if (lastH1) links.push({ source: lastH1.id, target: node.id });
      } else {
        // Se não tem heading claro, liga no último visto
        if (lastH2) links.push({ source: lastH2.id, target: node.id });
        else if (lastH1) links.push({ source: lastH1.id, target: node.id });
      }
    });

    return { nodes, links };
  }, [data]);

  return (
    <div className="absolute inset-0">
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="#0f172a"
        nodeLabel="title"
        nodeColor={(node: any) => {
          if (node.val === 3) return '#38bdf8'; // Sky blue for H1
          if (node.val === 2) return '#a78bfa'; // Purple for H2
          return '#34d399'; // Emerald for H3/others
        }}
        nodeRelSize={4}
        linkWidth={1.5}
        linkColor={() => 'rgba(255, 255, 255, 0.2)'}
        onNodeClick={(node: any) => onNodeClick(node as MocNode)}
        nodeThreeObject={(node: any) => {
          // Cria um sprite glow para os nós
          const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
              color: node.val === 3 ? '#38bdf8' : node.val === 2 ? '#a78bfa' : '#34d399',
              transparent: true,
              opacity: 0.8
            })
          );
          sprite.scale.set(node.val * 8, node.val * 8, 1);
          return sprite;
        }}
      />
    </div>
  );
};
