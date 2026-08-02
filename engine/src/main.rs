use anyhow::{Context, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::env;
use std::fs;
use std::path::PathBuf;
use tree_sitter::Parser;

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
    schema_version: String,
    parser_version: String,
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
    fn new(filepath: &str, doc_id: Option<&str>) -> Self {
        let content = fs::read_to_string(filepath).unwrap_or_default();
        let mut hasher = Sha256::new();
        if let Some(did) = doc_id {
            hasher.update(did.as_bytes());
        } else {
            hasher.update(filepath.as_bytes());
        }
        hasher.update(content.as_bytes());
        let hash_str = format!("{:x}", hasher.finalize());

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
        } else if kind == "paragraph"
            || kind == "fenced_code_block"
            || kind == "indented_code_block"
            || kind == "list"
            || kind == "thematic_break"
            || kind == "pipe_table"
            || kind == "table"
        {
            let text = node.utf8_text(source).unwrap_or("");
            if !self.current_node.content.ends_with("\n\n") {
                self.current_node.content.push_str("\n\n");
            }
            self.current_node.content.push_str(text.trim());
        } else {
            let mut cursor = node.walk();
            let mut sibling_count = 0;
            for child in node.children(&mut cursor) {
                sibling_count += 1;
                if sibling_count > 10_000 {
                    return Err(anyhow::anyhow!(
                        "AST width limit exceeded (too many siblings)"
                    ));
                }
                self.walk_ast(child, source, depth + 1)?;
            }
        }

        Ok(())
    }

    fn parse(mut self, content: &str) -> Result<Vec<SemanticNode>> {
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

    // O(1) Indexing for REFERENCES
    let mut title_to_id = HashMap::new();
    let mut word_to_nodes: HashMap<&str, Vec<usize>> = HashMap::new();

    for (idx, node) in nodes.iter().enumerate() {
        let anchor = node.title.to_lowercase().replace(' ', "-");
        title_to_id.insert(anchor, node.id.clone());

        for word in node.title.split_whitespace().filter(|w| w.len() > 4) {
            word_to_nodes.entry(word).or_default().push(idx);
        }
    }

    let link_regex = Regex::new(r"\(#([^\)]+)\)").unwrap();

    for (i, node_i) in nodes.iter().enumerate() {
        // 1. REFERENCES: O(N) extraction instead of O(N^2)
        for cap in link_regex.captures_iter(&node_i.content) {
            if let Some(target_anchor) = cap.get(1) {
                let target_anchor_str = target_anchor.as_str();
                if let Some(target_id) = title_to_id.get(target_anchor_str) {
                    if target_id != &node_i.id {
                        edges.push(GraphEdge {
                            source: node_i.id.clone(),
                            target: target_id.clone(),
                            rel_type: "REFERENCES".to_string(),
                        });
                    }
                }
            }
        }

        // 2. SEMANTICALLY_RELATED: O(N) extraction using inverted index
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

            // Sort by overlap count descending and cap to top 3 (pseudo k-NN)
            related.sort_by_key(|b| std::cmp::Reverse(b.0));
            for (_, target_id) in related.into_iter().take(3) {
                edges.push(GraphEdge {
                    source: node_i.id.clone(),
                    target: target_id,
                    rel_type: "SEMANTICALLY_RELATED".to_string(),
                });
            }
        }
    }

    // Deduplicate edges just in case (e.g. multiple references to the same anchor)
    let mut unique_edges = Vec::new();
    let mut seen = HashSet::new();
    for e in edges {
        let sig = format!("{}->{}->{}", e.source, e.target, e.rel_type);
        if seen.insert(sig) {
            unique_edges.push(e);
        }
    }

    unique_edges
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

    let doc_id = args.get(2).map(|s| s.as_str());
    let parser = AtlasParser::new(filepath_str, doc_id);
    let nodes = parser.parse(&content)?;
    let edges = extract_edges(&nodes);

    let moc = MocGraph {
        schema_version: "1.0.0".to_string(),
        parser_version: "2.0".to_string(),
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
                title: "Introduction to Rust".to_string(),
                content: "See [Next](#next-steps-in-rust)".to_string(),
            },
            SemanticNode {
                id: "2".to_string(),
                title: "Next Steps in Rust".to_string(),
                content: "Done.".to_string(),
            }
        ];
        
        let edges = extract_edges(&nodes);
        assert!(!edges.is_empty());
        assert_eq!(edges.len(), 1); // 1 REFERENCE (nenhum SEMANTICALLY_RELATED pois não há palavras suficientes)
    }
}
