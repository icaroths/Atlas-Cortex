use serde::{Serialize, Deserialize};
use std::fs;
use std::path::PathBuf;
use std::env;
use tree_sitter::Parser;
use anyhow::{Context, Result};

#[derive(Serialize, Deserialize, Debug)]
struct SemanticNode {
    id: usize,
    title: String,
    content: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct MocGraph {
    nodes: Vec<SemanticNode>,
}

struct AtlasParser {
    nodes: Vec<SemanticNode>,
    current_node: SemanticNode,
    node_id: usize,
}

impl AtlasParser {
    fn new() -> Self {
        Self {
            nodes: Vec::new(),
            current_node: SemanticNode {
                id: 0,
                title: "root".to_string(),
                content: String::new(),
            },
            node_id: 0,
        }
    }

    fn walk_ast(&mut self, node: tree_sitter::Node, source: &[u8]) -> Result<()> {
        let kind = node.kind();
        
        if kind == "atx_heading" || kind == "setext_heading" {
            // Push the previous section if it has content
            if !self.current_node.content.trim().is_empty() {
                self.nodes.push(SemanticNode {
                    id: self.current_node.id,
                    title: self.current_node.title.clone(),
                    content: self.current_node.content.trim().to_string(),
                });
            }
            
            self.node_id += 1;
            self.current_node.id = self.node_id;
            
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
                self.walk_ast(child, source)?;
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
        
        self.walk_ast(root, content.as_bytes())?;

        // Push the last node
        if !self.current_node.content.trim().is_empty() {
            self.current_node.content = self.current_node.content.trim().to_string();
            self.nodes.push(self.current_node);
        }

        Ok(self.nodes)
    }
}

fn main() -> Result<()> {
    println!("Atlas Cortex Engine V2 (Rust - Tree-Sitter AST)");
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        println!("Usage: engine <path_to_markdown>");
        return Ok(());
    }

    let filepath = PathBuf::from(&args[1]);
    if !filepath.exists() {
        anyhow::bail!("File not found: {:?}", filepath);
    }

    let content = fs::read_to_string(&filepath).context("Failed to read file")?;
    
    let parser = AtlasParser::new();
    let nodes = parser.parse(&content)?;
    
    let moc = MocGraph { nodes };
    let json_output = serde_json::to_string_pretty(&moc).context("Failed to serialize to JSON")?;
    
    let out_path = filepath.with_extension("moc.json");
    fs::write(&out_path, json_output).context("Failed to write output")?;
    
    println!("Atomic Ingestion complete: generated {} AST-backed semantic nodes at {:?}", moc.nodes.len(), out_path);
    
    Ok(())
}
