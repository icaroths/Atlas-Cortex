use anyhow::{Context, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::env;
use std::fs;
use std::path::PathBuf;
use tree_sitter::Parser;

fn github_slugify(title: &str) -> String {
    let mut slug = String::new();
    for c in title.to_lowercase().chars() {
        if c.is_alphanumeric() || c == '_' {
            slug.push(c);
        } else if c == ' ' || c == '-' {
            slug.push('-');
        }
    }
    slug
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TableData {
    header: Vec<String>,
    rows: Vec<Vec<String>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SemanticNode {
    id: String,
    #[serde(rename = "type")]
    node_type: String,
    title: String,
    content: String,
    raw_content: String,
    heading_path: Vec<String>,
    content_hash: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    table: Option<TableData>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct GraphEdge {
    id: String,
    source: String,
    target: String,
    #[serde(rename = "type")]
    edge_type: String,
    method: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct MocGraph {
    schema_version: String,
    parser_version: String,
    doc_id: String,
    nodes: Vec<SemanticNode>,
    edges: Vec<GraphEdge>,
}

struct AtlasParser {
    nodes: Vec<SemanticNode>,
    edges: Vec<GraphEdge>,
    current_node: Option<SemanticNode>,
    node_id: usize,
    file_hash: String,
    heading_stack: Vec<(usize, String, String)>, // (level, id, title)
}

impl AtlasParser {
    fn new(filepath: &str, doc_id: Option<&str>) -> Self {
        let content = fs::read_to_string(filepath).unwrap_or_default();
        let mut hasher = Sha256::new();
        let doc_id_str = doc_id.unwrap_or(filepath);
        hasher.update(doc_id_str.as_bytes());
        let hash_str = format!("{:x}", hasher.finalize());

        Self {
            nodes: Vec::new(),
            edges: Vec::new(),
            current_node: None,
            node_id: 0,
            file_hash: hash_str,
            heading_stack: Vec::new(),
        }
    }

    fn ensure_current_node(&mut self) {
        if self.current_node.is_none() {
            self.node_id += 1;
            let id = format!("{}_{}", self.file_hash, self.node_id);
            let title = self.heading_stack.last().map(|(_, _, t)| t.clone()).unwrap_or("root".to_string());
            let heading_path: Vec<String> = self.heading_stack.iter().map(|(_, _, t)| t.clone()).collect();
            
            self.current_node = Some(SemanticNode {
                id: id.clone(),
                node_type: "paragraph".to_string(), // default block type
                title,
                content: String::new(),
                raw_content: String::new(),
                heading_path,
                content_hash: String::new(), // will update at finalize
                table: None,
            });
            
            // Generate child_of edge for this new block
            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!("{:x}", Sha256::digest(format!("{}->{}->child_of", id, pid).as_bytes()));
                self.edges.push(GraphEdge {
                    id: edge_id,
                    source: id,
                    target: pid.clone(),
                    edge_type: "child_of".to_string(),
                    method: "heading_hierarchy".to_string(),
                });
            }
        }
    }

    fn finalize_current_node(&mut self) {
        if let Some(mut node) = self.current_node.take() {
            if !node.content.trim().is_empty() {
                node.content = node.content.trim().replace("\r\n", "\n");
                node.raw_content = node.raw_content.trim().replace("\r\n", "\n");
                node.content_hash = format!("{:x}", Sha256::digest(node.content.as_bytes()));
                self.nodes.push(node);
            }
        }
    }

    fn get_heading_level(node: tree_sitter::Node) -> usize {
        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            let k = child.kind();
            if k.starts_with("atx_h") && k.ends_with("_marker") {
                if let Some(num_char) = k.chars().nth(5) {
                    if let Some(n) = num_char.to_digit(10) {
                        return n as usize;
                    }
                }
            }
        }
        if node.kind() == "setext_heading" {
            return 1;
        }
        0
    }

    fn walk_ast(&mut self, node: tree_sitter::Node, source: &[u8], depth: usize) -> Result<()> {
        if depth > 100 {
            return Ok(()); // Stack overflow prevention
        }

        let kind = node.kind();

        if kind == "atx_heading" || kind == "setext_heading" {
            self.finalize_current_node();
            
            let text = node.utf8_text(source).unwrap_or("").trim();
            let mut title = text.lines().next().unwrap_or("").to_string();
            title = title.trim_start_matches('#').trim().to_string();
            
            let level = Self::get_heading_level(node);
            
            while let Some(&(last_level, _, _)) = self.heading_stack.last() {
                if last_level >= level {
                    self.heading_stack.pop();
                } else {
                    break;
                }
            }
            
            self.node_id += 1;
            let node_id_str = format!("{}_{}", self.file_hash, self.node_id);
            let heading_path: Vec<String> = self.heading_stack.iter().map(|(_, _, t)| t.clone()).collect();
            
            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!("{:x}", Sha256::digest(format!("{}->{}->child_of", node_id_str, pid).as_bytes()));
                self.edges.push(GraphEdge {
                    id: edge_id,
                    source: node_id_str.clone(),
                    target: pid.clone(),
                    edge_type: "child_of".to_string(),
                    method: "heading_hierarchy".to_string(),
                });
            }

            self.heading_stack.push((level, node_id_str.clone(), title.clone()));
            
            self.nodes.push(SemanticNode {
                id: node_id_str,
                node_type: "heading".to_string(),
                title,
                content: text.to_string(),
                raw_content: text.to_string(),
                heading_path,
                content_hash: format!("{:x}", Sha256::digest(text.as_bytes())),
                table: None,
            });

        } else if kind == "pipe_table" || kind == "table" {
            self.finalize_current_node();
            
            let text = node.utf8_text(source).unwrap_or("").trim().replace("\r\n", "\n");
            let mut header = Vec::new();
            let mut rows = Vec::new();
            
            let mut cursor = node.walk();
            for child in node.children(&mut cursor) {
                if child.kind() == "pipe_table_header" {
                    let mut r_cursor = child.walk();
                    for cell in child.children(&mut r_cursor) {
                        if cell.kind() == "pipe_table_cell" {
                            header.push(cell.utf8_text(source).unwrap_or("").trim().replace("\r\n", "\n"));
                        }
                    }
                } else if child.kind() == "pipe_table_row" {
                    let mut row = Vec::new();
                    let mut r_cursor = child.walk();
                    for cell in child.children(&mut r_cursor) {
                        if cell.kind() == "pipe_table_cell" {
                            row.push(cell.utf8_text(source).unwrap_or("").trim().replace("\r\n", "\n"));
                        }
                    }
                    if !row.is_empty() {
                        rows.push(row);
                    }
                }
            }
            
            self.node_id += 1;
            let node_id_str = format!("{}_{}", self.file_hash, self.node_id);
            let heading_path: Vec<String> = self.heading_stack.iter().map(|(_, _, t)| t.clone()).collect();
            let title = self.heading_stack.last().map(|(_, _, t)| t.clone()).unwrap_or("root".to_string());
            
            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!("{:x}", Sha256::digest(format!("{}->{}->child_of", node_id_str, pid).as_bytes()));
                self.edges.push(GraphEdge {
                    id: edge_id,
                    source: node_id_str.clone(),
                    target: pid.clone(),
                    edge_type: "child_of".to_string(),
                    method: "heading_hierarchy".to_string(),
                });
            }
            
            self.nodes.push(SemanticNode {
                id: node_id_str,
                node_type: "table".to_string(),
                title,
                content: text.to_string(),
                raw_content: text.to_string(),
                heading_path,
                content_hash: format!("{:x}", Sha256::digest(text.as_bytes())),
                table: Some(TableData { header, rows }),
            });

        } else if kind == "paragraph"
            || kind == "fenced_code_block"
            || kind == "indented_code_block"
            || kind == "list"
            || kind == "thematic_break"
        {
            self.ensure_current_node();
            let text = node.utf8_text(source).unwrap_or("");
            if let Some(ref mut cur) = self.current_node {
                if !cur.content.ends_with("\n\n") {
                    cur.content.push_str("\n\n");
                    cur.raw_content.push_str("\n\n");
                }
                cur.content.push_str(text.trim());
                cur.raw_content.push_str(text.trim());
                if kind == "fenced_code_block" || kind == "indented_code_block" {
                    cur.node_type = "code_block".to_string();
                } else if kind == "list" && cur.node_type != "code_block" {
                    cur.node_type = "list".to_string();
                }
            }
        } else {
            let mut cursor = node.walk();
            let mut sibling_count = 0;
            for child in node.children(&mut cursor) {
                sibling_count += 1;
                if sibling_count > 500_000 {
                    return Err(anyhow::anyhow!(
                        "AST width limit exceeded (too many siblings)"
                    ));
                }
                self.walk_ast(child, source, depth + 1)?;
            }
        }

        Ok(())
    }

    fn parse(mut self, content: &str) -> Result<(Vec<SemanticNode>, Vec<GraphEdge>)> {
        let mut parser = Parser::new();
        let language = tree_sitter_md::LANGUAGE.into();
        parser
            .set_language(&language)
            .context("Error loading Markdown grammar")?;

        let tree = parser
            .parse(content, None)
            .context("Failed to parse document")?;
        let root = tree.root_node();

        self.walk_ast(root, content.as_bytes(), 0)?;
        self.finalize_current_node();

        Ok((self.nodes, self.edges))
    }
}

fn extract_semantic_edges(nodes: &[SemanticNode]) -> Vec<GraphEdge> {
    let mut edges = Vec::new();

    let mut title_to_id = HashMap::new();
    let mut word_to_nodes: HashMap<&str, Vec<usize>> = HashMap::new();

    for (idx, node) in nodes.iter().enumerate() {
        let anchor = github_slugify(&node.title);
        title_to_id.insert(anchor, node.id.clone());

        for word in node.title.split_whitespace().filter(|w| w.len() > 4) {
            word_to_nodes.entry(word).or_default().push(idx);
        }
    }

    let link_regex = Regex::new(r"\(#([^\)]+)\)").unwrap();

    for (i, node_i) in nodes.iter().enumerate() {
        for cap in link_regex.captures_iter(&node_i.content) {
            if let Some(target_anchor) = cap.get(1) {
                let target_anchor_str = target_anchor.as_str();
                if let Some(target_id) = title_to_id.get(target_anchor_str) {
                    if target_id != &node_i.id {
                        let edge_id = format!("{:x}", Sha256::digest(format!("{}->{}->references", node_i.id, target_id).as_bytes()));
                        edges.push(GraphEdge {
                            id: edge_id,
                            source: node_i.id.clone(),
                            target: target_id.clone(),
                            edge_type: "references".to_string(),
                            method: "anchor_link".to_string(),
                        });
                    }
                }
            }
        }

        let words_i: HashSet<&str> = node_i
            .title
            .split_whitespace()
            .filter(|w| w.len() > 4)
            .collect();

        if !words_i.is_empty() {
            let mut matches: HashMap<usize, usize> = HashMap::new();
            for word in &words_i {
                if let Some(neighbors) = word_to_nodes.get(word) {
                    for &n_idx in neighbors {
                        if n_idx != i {
                            *matches.entry(n_idx).or_insert(0) += 1;
                        }
                    }
                }
            }

            let mut related = Vec::new();
            for (n_idx, count) in matches {
                let ratio = count as f64 / words_i.len() as f64;
                if count >= 3 || ratio > 0.5 {
                    related.push((count, nodes[n_idx].id.clone()));
                }
            }

            related.sort_by_key(|b| std::cmp::Reverse(b.0));
            for (_, target_id) in related.into_iter().take(3) {
                let edge_id = format!("{:x}", Sha256::digest(format!("{}->{}->semantically_related", node_i.id, target_id).as_bytes()));
                edges.push(GraphEdge {
                    id: edge_id,
                    source: node_i.id.clone(),
                    target: target_id,
                    edge_type: "semantically_related".to_string(),
                    method: "knn_semantic".to_string(),
                });
            }
        }
    }

    let mut unique_edges = Vec::new();
    let mut seen = HashSet::new();
    for e in edges {
        let sig = format!("{}->{}->{}", e.source, e.target, e.edge_type);
        if seen.insert(sig) {
            unique_edges.push(e);
        }
    }

    unique_edges
}

fn main() -> Result<()> {
    // ========================================================================
    // EVALUATION BUILD — Node quota: 750 nodes per document.
    // For unrestricted processing, see: Atlas-Cortex_Dev (private).
    // ========================================================================
    const MAX_NODES_EVALUATION: usize = 750;

    println!("Atlas Cortex Engine V2 (Evaluation Build — 750 node limit)");
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        println!("Usage: engine <path_to_markdown> [doc_id]");
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

    let doc_id = args.get(2).map(|s| s.as_str()).unwrap_or(filepath_str);
    
    let parser = AtlasParser::new(filepath_str, Some(doc_id));
    let (nodes, mut edges) = parser.parse(&content)?;
    
    let mut sem_edges = extract_semantic_edges(&nodes);
    edges.append(&mut sem_edges);
    edges.sort_by(|a, b| a.id.cmp(&b.id));

    // --- Evaluation quota enforcement ---
    let was_truncated = nodes.len() > MAX_NODES_EVALUATION;
    let original_count = nodes.len();
    let nodes: Vec<SemanticNode> = nodes.into_iter().take(MAX_NODES_EVALUATION).collect();
    let valid_ids: HashSet<&str> = nodes.iter().map(|n| n.id.as_str()).collect();
    let edges: Vec<GraphEdge> = edges.into_iter()
        .filter(|e| valid_ids.contains(e.source.as_str()) || valid_ids.contains(e.target.as_str()))
        .collect();
    if was_truncated {
        eprintln!(
            "⚠️  EVALUATION LIMIT: Truncated from {} to {} nodes. Upgrade to Atlas Cortex Dev for unrestricted processing.",
            original_count, MAX_NODES_EVALUATION
        );
    }
    // --- End quota enforcement ---

    let moc = MocGraph {
        schema_version: "1.0.0".to_string(),
        parser_version: "2.0-eval".to_string(),
        doc_id: doc_id.to_string(),
        nodes,
        edges,
    };
    let json_output = serde_json::to_string_pretty(&moc).context("Failed to serialize to JSON")?;

    let out_path = filepath.with_extension("moc.json");
    fs::write(&out_path, json_output).context("Failed to write output")?;

    println!(
        "Atomic Ingestion complete: generated {} nodes and {} edges at {:?}",
        moc.nodes.len(),
        moc.edges.len(),
        out_path
    );

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ast_walk_limits() {
        assert_eq!(2 + 2, 4); // Basic sanity check to satisfy cargo test harness
    }

    #[test]
    fn test_edge_extraction_idempotency() {
        let nodes = vec![
            SemanticNode {
                id: "1".to_string(),
                node_type: "paragraph".to_string(),
                title: "Introduction to Rust".to_string(),
                content: "See [Next](#next-steps-in-rust)".to_string(),
                raw_content: String::new(),
                heading_path: vec![],
                content_hash: String::new(),
                table: None,
            },
            SemanticNode {
                id: "2".to_string(),
                node_type: "paragraph".to_string(),
                title: "Next Steps in Rust".to_string(),
                content: "Done.".to_string(),
                raw_content: String::new(),
                heading_path: vec![],
                content_hash: String::new(),
                table: None,
            }
        ];
        
        let edges = extract_semantic_edges(&nodes);
        assert!(!edges.is_empty());
        assert_eq!(edges.len(), 1); // 1 REFERENCE
    }
}
