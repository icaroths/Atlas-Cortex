use serde::{Serialize, Deserialize};
use std::fs;
use std::path::PathBuf;
use std::env;
use std::collections::HashSet;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use tree_sitter::Parser;
use anyhow::{Context, Result};

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SemanticNode {
    id: String,
    title: String,
    content: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct GraphEdge {
    source: String,
    target: String,
    rel_type: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct MocGraph {
    nodes: Vec<SemanticNode>,
    edges: Vec<GraphEdge>,
}

struct AtlasParser {
    nodes: Vec<SemanticNode>,
    current_node: SemanticNode,
    node_id: usize,
    file_hash: String,
}

impl AtlasParser {
    fn new(filepath: &str) -> Self {
        let mut hasher = DefaultHasher::new();
        filepath.hash(&mut hasher);
        let hash_str = format!("{:x}", hasher.finish());

        Self {
            nodes: Vec::new(),
            current_node: SemanticNode {
                id: format!("{}_root", hash_str),
                title: "root".to_string(),
                content: String::new(),
            },
            node_id: 0,
            file_hash: hash_str,
        }
    }

    fn walk_ast(&mut self, node: tree_sitter::Node, source: &[u8], depth: usize) -> Result<()> {
        if depth > 100 {
            return Ok(()); // Prevents Stack Overflow on excessively nested markdown
        }

        let kind = node.kind();
        
        if kind == "atx_heading" || kind == "setext_heading" {
            if !self.current_node.content.trim().is_empty() {
                self.nodes.push(SemanticNode {
                    id: self.current_node.id.clone(),
                    title: self.current_node.title.clone(),
                    content: self.current_node.content.trim().to_string(),
                });
            }
            
            self.node_id += 1;
            self.current_node.id = format!("{}_{}", self.file_hash, self.node_id);
            
            let text = node.utf8_text(source).unwrap_or("");
            self.current_node.title = text.lines().next().unwrap_or("").trim().to_string();
            self.current_node.content = format!("{}\n", text.trim());
            
        } else if kind == "paragraph" || kind == "fenced_code_block" || kind == "indented_code_block" || kind == "list" || kind == "thematic_break" {
            let text = node.utf8_text(source).unwrap_or("");
            if !self.current_node.content.ends_with("\n\n") {
                self.current_node.content.push_str("\n\n");
            }
            self.current_node.content.push_str(text.trim());
        } else {
            let mut cursor = node.walk();
            for child in node.children(&mut cursor) {
                self.walk_ast(child, source, depth + 1)?;
            }
        }
        
        Ok(())
    }

    fn parse(mut self, content: &str) -> Result<Vec<SemanticNode>> {
        let mut parser = Parser::new();
        let language = tree_sitter_md::LANGUAGE.into();
        parser.set_language(&language).context("Error loading Markdown grammar")?;
        
        let tree = parser.parse(content, None).context("Failed to parse document")?;
        let root = tree.root_node();
        
        self.walk_ast(root, content.as_bytes(), 0)?;

        // Push the last node
        if !self.current_node.content.trim().is_empty() {
            self.current_node.content = self.current_node.content.trim().to_string();
            self.nodes.push(self.current_node);
        }

        Ok(self.nodes)
    }
}

fn extract_edges(nodes: &[SemanticNode]) -> Vec<GraphEdge> {
    let mut edges = Vec::new();
    
    let titles: Vec<String> = nodes.iter()
        .map(|n| n.title.to_lowercase().replace(' ', "-"))
        .collect();

    for i in 0..nodes.len() {
        let node_i = &nodes[i];
        
        // 1. REFERENCES: Look for anchor links
        for j in 0..nodes.len() {
            if i == j { continue; }
            let anchor = format!("(#{})", titles[j]);
            if node_i.content.contains(&anchor) {
                edges.push(GraphEdge {
                    source: node_i.id.clone(),
                    target: nodes[j].id.clone(),
                    rel_type: "REFERENCES".to_string(),
                });
            }
        }
        
        // 2. SEMANTICALLY_RELATED: Stricter heuristic (k-NN proxy)
        let words_i: HashSet<&str> = node_i.title.split_whitespace()
            .filter(|w| w.len() > 4)
            .collect();
            
        if words_i.is_empty() { continue; }

        let mut related = Vec::new();
        for j in 0..nodes.len() {
            if i == j { continue; }
            let words_j: HashSet<&str> = nodes[j].title.split_whitespace()
                .filter(|w| w.len() > 4)
                .collect();
                
            let intersection = words_i.intersection(&words_j).count();
            // Stricter rule: require at least 3 matching significant words, or 50% overlap
            let ratio = intersection as f64 / words_i.len() as f64;
            if intersection >= 3 || ratio > 0.5 {
                related.push((intersection, nodes[j].id.clone()));
            }
        }
        
        // Sort by overlap count descending and cap to top 3 (pseudo k-NN)
        related.sort_by(|a, b| b.0.cmp(&a.0));
        for (_, target_id) in related.into_iter().take(3) {
            edges.push(GraphEdge {
                source: node_i.id.clone(),
                target: target_id,
                rel_type: "SEMANTICALLY_RELATED".to_string(),
            });
        }
    }
    
    edges
}

fn main() -> Result<()> {
    println!("Atlas Cortex Engine V2 (Rust - Tree-Sitter AST & GraphRAG)");
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        println!("Usage: engine <path_to_markdown>");
        return Ok(());
    }

    let filepath_str = &args[1];
    let filepath = PathBuf::from(filepath_str);
    if !filepath.exists() {
        anyhow::bail!("File not found: {:?}", filepath);
    }

    let metadata = fs::metadata(&filepath).context("Failed to read metadata")?;
    if metadata.len() > 50 * 1024 * 1024 {
        anyhow::bail!("File too large (> 50MB). Chunk file first to avoid OOM.");
    }

    let content = fs::read_to_string(&filepath).context("Failed to read file")?;
    
    let parser = AtlasParser::new(filepath_str);
    let nodes = parser.parse(&content)?;
    let edges = extract_edges(&nodes);
    
    let moc = MocGraph { nodes, edges };
    let json_output = serde_json::to_string_pretty(&moc).context("Failed to serialize to JSON")?;
    
    let out_path = filepath.with_extension("moc.json");
    fs::write(&out_path, json_output).context("Failed to write output")?;
    
    println!("Atomic Ingestion complete: generated {} nodes and {} edges at {:?}", moc.nodes.len(), moc.edges.len(), out_path);
    
    Ok(())
}
