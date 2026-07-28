use serde::{Serialize, Deserialize};
use std::fs;
use std::path::PathBuf;
use std::env;
use tree_sitter::{Parser, Node};

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
    let mut parser = Parser::new();
    let language = tree_sitter_md::LANGUAGE.into();
    parser.set_language(&language).expect("Error loading Markdown grammar");
    let tree = parser.parse(content, None).unwrap();
    let root = tree.root_node();
    
    let mut nodes = Vec::new();
    let mut current_node = SemanticNode {
        id: 0,
        title: "root".to_string(),
        content: String::new(),
    };
    let mut node_id = 0;
    
    let source = content.as_bytes();
    
    fn walk_ast(node: tree_sitter::Node, source: &[u8], current: &mut SemanticNode, nodes: &mut Vec<SemanticNode>, node_id: &mut usize) {
        let kind = node.kind();
        if kind == "atx_heading" || kind == "setext_heading" {
            if !current.content.trim().is_empty() {
                nodes.push(SemanticNode {
                    id: current.id,
                    title: current.title.clone(),
                    content: current.content.clone(),
                });
            }
            *node_id += 1;
            current.id = *node_id;
            let text = node.utf8_text(source).unwrap_or("");
            current.title = text.lines().next().unwrap_or("").trim().to_string();
            current.content = format!("{}\n", text);
        } else if kind == "paragraph" || kind == "fenced_code_block" || kind == "indented_code_block" || kind == "list" || kind == "thematic_break" {
            let text = node.utf8_text(source).unwrap_or("");
            current.content.push_str(text);
            current.content.push('\n');
            current.content.push('\n');
        } else {
            let mut cursor = node.walk();
            for child in node.children(&mut cursor) {
                walk_ast(child, source, current, nodes, node_id);
            }
        }
    }

    walk_ast(root, source, &mut current_node, &mut nodes, &mut node_id);

    if !current_node.content.trim().is_empty() {
        nodes.push(current_node);
    }

    nodes
}

fn main() {
    println!("Atlas Cortex Engine V2 (Rust - Tree-Sitter AST)");
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
    
    println!("Atomic Ingestion complete: generated {} AST-backed semantic nodes at {:?}", moc.nodes.len(), out_path);
}
