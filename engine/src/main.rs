// Atlas Cortex Engine — CLI Binary (Thin Wrapper)
//
// This binary is a thin CLI wrapper around the library (lib.rs).
// All parsing logic lives in lib.rs for reusability via PyO3.

use anyhow::{Context, Result};
use std::env;
use std::fs;
use std::path::PathBuf;

use _engine::{AtlasParser, MocGraph, extract_semantic_edges};

fn main() -> Result<()> {
    // ========================================================================
    // ENTERPRISE BUILD — 100% Unrestricted Capacity.
    // ========================================================================
    println!("Atlas Cortex Engine V2 (Enterprise Build — 100% Capacity)");
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

    let moc = MocGraph {
        schema_version: "1.0.0".to_string(),
        parser_version: "2.0".to_string(),
        doc_id: doc_id.to_string(),
        truncated: false,
        original_node_count: None,
        truncated_node_count: None,
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
