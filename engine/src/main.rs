use serde::{Serialize, Deserialize};
use std::fs;
use std::path::PathBuf;
use std::env;
use tree_sitter::{Parser, Language};

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

fn parse_markdown_topologically(content: &str) -> Vec<SemanticNode> {
    // Tree-sitter AST Injection (Placeholder for grammar)
    let mut parser = Parser::new();
    // let language = tree_sitter_markdown::language();
    // parser.set_language(&language).expect("Error loading Markdown grammar");
    // let tree = parser.parse(content, None).unwrap();
    // println!("AST Injected. Root node: {:?}", tree.root_node().kind());

    let mut nodes = Vec::new();
    let mut current_node = SemanticNode {
        id: 0,
        title: "root".to_string(),
        content: String::new(),
    };
    let mut node_id = 0;

    for line in content.lines() {
        if line.starts_with('#') {
            if !current_node.content.trim().is_empty() {
                nodes.push(current_node);
            }
            node_id += 1;
            current_node = SemanticNode {
                id: node_id,
                title: line.trim().to_string(),
                content: format!("{}\n", line),
            };
        } else {
            current_node.content.push_str(line);
            current_node.content.push('\n');
        }
    }

    if !current_node.content.trim().is_empty() {
        nodes.push(current_node);
    }

    nodes
}

fn main() {
    println!("Atlas Cortex Engine V2 (Rust)");
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        println!("Usage: engine <path_to_markdown>");
        return;
    }

    let filepath = PathBuf::from(&args[1]);
    if !filepath.exists() {
        println!("File not found: {:?}", filepath);
        return;
    }

    let content = fs::read_to_string(&filepath).expect("Failed to read file");
    let nodes = parse_markdown_topologically(&content);
    
    let moc = MocGraph { nodes };
    let json_output = serde_json::to_string_pretty(&moc).expect("Failed to serialize to JSON");
    
    let out_path = filepath.with_extension("moc.json");
    fs::write(&out_path, json_output).expect("Failed to write output");
    
    println!("Atomic Ingestion complete: generated {} semantic nodes at {:?}", moc.nodes.len(), out_path);
}
