// Atlas Cortex Engine — Library Module (Fase 12)

#![allow(deprecated)]
#![allow(unsafe_op_in_unsafe_fn)]
#![allow(clippy::collapsible_if)]
//
// This module exposes the core parsing logic as reusable functions,
// consumable both by the CLI binary (main.rs) and by PyO3 (Python native bindings).
//
// Architecture: lib.rs owns all parsing logic; main.rs is a thin CLI wrapper.

use anyhow::{Context, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};

pub fn github_slugify(title: &str) -> String {
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
pub struct TableData {
    pub header: Vec<String>,
    pub rows: Vec<Vec<String>>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SemanticNode {
    pub id: String,
    #[serde(rename = "type")]
    pub node_type: String,
    pub title: String,
    pub content: String,
    pub raw_content: String,
    pub heading_path: Vec<String>,
    pub content_hash: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub table: Option<TableData>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GraphEdge {
    pub id: String,
    pub source: String,
    pub target: String,
    #[serde(rename = "type")]
    pub edge_type: String,
    pub method: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct MocGraph {
    pub schema_version: String,
    pub parser_version: String,
    pub doc_id: String,
    pub truncated: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_node_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub truncated_node_count: Option<usize>,
    pub nodes: Vec<SemanticNode>,
    pub edges: Vec<GraphEdge>,
}

pub struct AtlasParser {
    pub nodes: Vec<SemanticNode>,
    pub edges: Vec<GraphEdge>,
    current_node: Option<SemanticNode>,
    node_id: usize,
    file_hash: String,
    heading_stack: Vec<(usize, String, String)>, // (level, id, title)
}

impl AtlasParser {
    pub fn new(filepath: &str, doc_id: Option<&str>) -> Self {
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
            let title = self
                .heading_stack
                .last()
                .map(|(_, _, t)| t.clone())
                .unwrap_or("root".to_string());
            let heading_path: Vec<String> = self
                .heading_stack
                .iter()
                .map(|(_, _, t)| t.clone())
                .collect();

            self.current_node = Some(SemanticNode {
                id: id.clone(),
                node_type: "paragraph".to_string(),
                title,
                content: String::new(),
                raw_content: String::new(),
                heading_path,
                content_hash: String::new(),
                table: None,
            });

            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!(
                    "{:x}",
                    Sha256::digest(format!("{}->{}->child_of", id, pid).as_bytes())
                );
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
            return Ok(());
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
            let heading_path: Vec<String> = self
                .heading_stack
                .iter()
                .map(|(_, _, t)| t.clone())
                .collect();

            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!(
                    "{:x}",
                    Sha256::digest(format!("{}->{}->child_of", node_id_str, pid).as_bytes())
                );
                self.edges.push(GraphEdge {
                    id: edge_id,
                    source: node_id_str.clone(),
                    target: pid.clone(),
                    edge_type: "child_of".to_string(),
                    method: "heading_hierarchy".to_string(),
                });
            }

            self.heading_stack
                .push((level, node_id_str.clone(), title.clone()));

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

            let text = node
                .utf8_text(source)
                .unwrap_or("")
                .trim()
                .replace("\r\n", "\n");
            let mut header = Vec::new();
            let mut rows = Vec::new();

            let mut cursor = node.walk();
            for child in node.children(&mut cursor) {
                if child.kind() == "pipe_table_header" {
                    let mut r_cursor = child.walk();
                    for cell in child.children(&mut r_cursor) {
                        if cell.kind() == "pipe_table_cell" {
                            header.push(
                                cell.utf8_text(source)
                                    .unwrap_or("")
                                    .trim()
                                    .replace("\r\n", "\n"),
                            );
                        }
                    }
                } else if child.kind() == "pipe_table_row" {
                    let mut row = Vec::new();
                    let mut r_cursor = child.walk();
                    for cell in child.children(&mut r_cursor) {
                        if cell.kind() == "pipe_table_cell" {
                            row.push(
                                cell.utf8_text(source)
                                    .unwrap_or("")
                                    .trim()
                                    .replace("\r\n", "\n"),
                            );
                        }
                    }
                    if !row.is_empty() {
                        rows.push(row);
                    }
                }
            }

            self.node_id += 1;
            let node_id_str = format!("{}_{}", self.file_hash, self.node_id);
            let heading_path: Vec<String> = self
                .heading_stack
                .iter()
                .map(|(_, _, t)| t.clone())
                .collect();
            let title = self
                .heading_stack
                .last()
                .map(|(_, _, t)| t.clone())
                .unwrap_or("root".to_string());

            if let Some((_, pid, _)) = self.heading_stack.last() {
                let edge_id = format!(
                    "{:x}",
                    Sha256::digest(format!("{}->{}->child_of", node_id_str, pid).as_bytes())
                );
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

    pub fn parse(mut self, content: &str) -> Result<(Vec<SemanticNode>, Vec<GraphEdge>)> {
        let mut parser = tree_sitter::Parser::new();
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

pub fn extract_semantic_edges(nodes: &[SemanticNode]) -> Vec<GraphEdge> {
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
                        let edge_id = format!(
                            "{:x}",
                            Sha256::digest(
                                format!("{}->{}->references", node_i.id, target_id).as_bytes()
                            )
                        );
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
                let edge_id = format!(
                    "{:x}",
                    Sha256::digest(
                        format!("{}->{}->semantically_related", node_i.id, target_id).as_bytes()
                    )
                );
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

/// High-level API: parse Markdown text and return a complete MocGraph.
pub fn parse_markdown(content: &str, doc_id: &str, parser_version: &str) -> Result<MocGraph> {
    let parser = AtlasParser::new("memory", Some(doc_id));
    let (nodes, mut edges) = parser.parse(content)?;

    let mut sem_edges = extract_semantic_edges(&nodes);
    edges.append(&mut sem_edges);
    edges.sort_by(|a, b| a.id.cmp(&b.id));

    Ok(MocGraph {
        schema_version: "1.0.0".to_string(),
        parser_version: parser_version.to_string(),
        doc_id: doc_id.to_string(),
        truncated: false,
        original_node_count: None,
        truncated_node_count: None,
        nodes,
        edges,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_github_slugify_basic() {
        assert_eq!(github_slugify("Hello World"), "hello-world");
        assert_eq!(github_slugify("Section 1.2"), "section-12");
    }

    #[test]
    fn test_github_slugify_special_chars() {
        assert_eq!(
            github_slugify("API & Data -- Test_1"),
            "api--data----test_1"
        );
    }

    #[test]
    fn test_parse_markdown_basic() {
        let content = "# Hello\n\nWorld";
        let result = parse_markdown(content, "test-doc", "2.0").unwrap();
        assert!(!result.nodes.is_empty());
        assert_eq!(result.doc_id, "test-doc");
        assert_eq!(result.schema_version, "1.0.0");
    }

    #[test]
    fn test_parse_markdown_deterministic() {
        let content = "# Title\n\nParagraph text.";
        let r1 = parse_markdown(content, "doc1", "2.0").unwrap();
        let r2 = parse_markdown(content, "doc1", "2.0").unwrap();
        assert_eq!(r1.nodes.len(), r2.nodes.len());
        assert_eq!(r1.edges.len(), r2.edges.len());
        for (n1, n2) in r1.nodes.iter().zip(r2.nodes.iter()) {
            assert_eq!(n1.id, n2.id);
            assert_eq!(n1.content_hash, n2.content_hash);
        }
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
            },
        ];

        let edges = extract_semantic_edges(&nodes);
        assert_eq!(edges.len(), 1);
        assert_eq!(edges[0].edge_type, "references");
    }

    #[test]
    fn test_atlas_parser_initialization() {
        let parser = AtlasParser::new("dummy.md", Some("doc_123"));
        assert_eq!(parser.nodes.len(), 0);
        assert_eq!(parser.edges.len(), 0);
        assert_eq!(parser.node_id, 0);
        assert!(!parser.file_hash.is_empty());
    }
}

// ============================================================================
// PyO3 Native Python Bindings
// ============================================================================
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (content, doc_id=None, parser_version=None))]
fn parse_text_native(
    content: String,
    doc_id: Option<String>,
    parser_version: Option<String>,
) -> PyResult<String> {
    let pv = parser_version.as_deref().unwrap_or("2.0");
    match parse_markdown(&content, doc_id.as_deref().unwrap_or(""), pv) {
        Ok(graph) => {
            let json = serde_json::to_string(&graph).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Serialization error: {}", e))
            })?;
            Ok(json)
        }
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "Parse error: {}",
            e
        ))),
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn _engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_text_native, m)?)?;
    Ok(())
}
