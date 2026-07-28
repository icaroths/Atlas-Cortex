import { useMemo, useRef, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

const Graph3D = () => {
  // Generate a mock Topological MOC graph
  const gData = useMemo(() => {
    const N = 80;
    const nodes = [...Array(N).keys()].map(i => ({ id: i, val: (Math.random() * 1.5) + 1 }));
    const links = [...Array(N).keys()]
      .filter(id => id)
      .map(id => ({
        source: id,
        target: Math.round(Math.random() * (id - 1))
      }));

    return { nodes, links };
  }, []);

  const fgRef = useRef<any>();

  useEffect(() => {
    let angle = 0;
    const distance = 250;
    
    const interval = setInterval(() => {
      if (fgRef.current) {
        fgRef.current.cameraPosition({
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle)
        });
        angle += Math.PI / 300;
      }
    }, 20);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ 
      width: '100%', 
      height: '400px', 
      borderRadius: '12px', 
      overflow: 'hidden',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      background: 'rgba(10, 10, 12, 0.8)'
    }}>
      <ForceGraph3D
        ref={fgRef}
        graphData={gData}
        nodeLabel="id"
        nodeAutoColorBy="group"
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={() => Math.random() * 0.01 + 0.005}
        backgroundColor="rgba(0,0,0,0)"
        nodeRelSize={4}
        linkColor={() => 'rgba(255, 255, 255, 0.2)'}
      />
    </div>
  );
};

export default Graph3D;
