import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import './App.css'

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // States para filtros e buscas
  const [allTypes, setAllTypes] = useState([])
  const [visibleTypes, setVisibleTypes] = useState(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  
  // Highlight states
  const [hoverNode, setHoverNode] = useState(null)
  const highlightNodes = useRef(new Set())
  const highlightLinks = useRef(new Set())

  const fgRef = useRef()

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target.result)
        if (!json.nodes || !json.edges) {
          throw new Error("Invalid .moc.json format. Missing 'nodes' or 'edges'.")
        }
        
        const gData = {
          nodes: json.nodes.map(n => ({ 
            id: n.id, 
            name: n.title, 
            type: n.type,
            val: 1
          })),
          links: json.edges.map(e => ({ 
            source: e.source, 
            target: e.target, 
            type: e.type 
          }))
        }
        
        const types = [...new Set(gData.nodes.map(n => n.type))]
        setAllTypes(types)
        setVisibleTypes(new Set(types))
        setGraphData(gData)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    reader.readAsText(file)
  }

  const handleNodeClick = useCallback(node => {
    const distance = 40;
    const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);

    fgRef.current.cameraPosition(
      { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, 
      node, 
      3000  
    );
  }, [fgRef]);

  const handleNodeHover = node => {
    highlightNodes.current.clear()
    highlightLinks.current.clear()
    if (node) {
      highlightNodes.current.add(node.id)
      graphData.links.forEach(link => {
        if ((link.source.id || link.source) === node.id || (link.target.id || link.target) === node.id) {
          highlightLinks.current.add(link)
          highlightNodes.current.add(link.source.id || link.source)
          highlightNodes.current.add(link.target.id || link.target)
        }
      })
    }

    setHoverNode(node || null)
  }

  const handleTypeToggle = (type) => {
    const nextVisible = new Set(visibleTypes)
    if (nextVisible.has(type)) {
      nextVisible.delete(type)
    } else {
      nextVisible.add(type)
    }
    setVisibleTypes(nextVisible)
  }

  const filteredData = useMemo(() => {
    if (graphData.nodes.length === 0) return { nodes: [], links: [] }

    const q = searchQuery.toLowerCase()
    
    // Filtrar os nós
    const visibleNodes = graphData.nodes.filter(node => 
      visibleTypes.has(node.type) && 
      (q === '' || node.name.toLowerCase().includes(q))
    )
    
    const visibleNodeIds = new Set(visibleNodes.map(n => n.id))

    // Filtrar arestas (apenas mostrar se ambos source e target estao visíveis)
    const visibleLinks = graphData.links.filter(link => {
      const sourceId = link.source.id || link.source
      const targetId = link.target.id || link.target
      return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId)
    })

    return { nodes: visibleNodes, links: visibleLinks }
  }, [graphData, visibleTypes, searchQuery])

  return (
    <div className="app-container">
      <div className="sidebar">
        <h1>Atlas Cortex V2</h1>
        <p>3D Semantic Graph Viewer</p>
        
        <div className="upload-section">
          <label className="upload-btn">
            Carregar .moc.json
            <input type="file" accept=".json" onChange={handleFileUpload} hidden />
          </label>
        </div>

        {loading && <p>Carregando grafo...</p>}
        {error && <p className="error">{error}</p>}
        
        {graphData.nodes.length > 0 && (
          <div className="filters-section">
            <div className="search-box">
              <input 
                type="text" 
                placeholder="Buscar por título..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <div className="types-filter">
              <h3>Filtros por Tipo</h3>
              {allTypes.map(type => (
                <label key={type} className="checkbox-label">
                  <input 
                    type="checkbox" 
                    checked={visibleTypes.has(type)}
                    onChange={() => handleTypeToggle(type)}
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="stats">
          <p>Nós visíveis: <strong>{filteredData.nodes.length}</strong> / {graphData.nodes.length}</p>
          <p>Arestas visíveis: <strong>{filteredData.links.length}</strong> / {graphData.links.length}</p>
        </div>
      </div>
      
      <div className="graph-container">
        {filteredData.nodes.length > 0 ? (
          <ForceGraph3D
            ref={fgRef}
            graphData={filteredData}
            nodeLabel="name"
            nodeAutoColorBy="type"
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            nodeRelSize={5}
            nodeColor={node => highlightNodes.current.has(node.id) ? node === hoverNode ? 'rgb(255,0,0,1)' : 'rgba(255,160,0,0.8)' : 'rgba(0,255,255,0.6)'}
            linkColor={link => highlightLinks.current.has(link) ? 'rgba(255,0,0,1)' : 'rgba(255,255,255,0.2)'}
            linkWidth={link => highlightLinks.current.has(link) ? 2 : 0.5}
          />
        ) : (
          <div className="empty-state">
            Nenhum grafo carregado ou todos os nós foram filtrados.
          </div>
        )}
      </div>
    </div>
  )
}

export default App
