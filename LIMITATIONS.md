# Atlas Cortex - Technical Limitations & Operational Boundaries

This document details the operational limits and architectural boundaries enforced in Atlas Cortex (Evaluation and Enterprise editions).

---

## 1. Node Limits

- **Evaluation Edition**: Enforces a strict maximum limit of **750 nodes** per parsed document. If a document yields more than 750 nodes, the AST parser truncates the output node list to 750 items, filtering invalid dangling edges and injecting `"truncated": true`, `"original_node_count"`, and `"truncated_node_count"` into the MOC JSON response.
- **Enterprise Edition**: Unrestricted node parsing capabilities.

---

## 2. Resource & Safety Constraints

- **File Size (OOM Guard)**: Enforces a maximum input file size limit of **50 MB**. Files exceeding 50 MB are rejected prior to AST construction to prevent process Out-Of-Memory (OOM) failures.
- **Subprocess Timeout**: Subprocess execution (Python -> Rust binary) enforces a hard timeout of **30 seconds** per document parse.
- **AST Depth Limit**: Maximum tree depth of **100** levels during AST traversal to prevent recursion stack overflow.
- **AST Sibling Limit**: Maximum **500,000** sibling nodes per tree level.

---

## 3. Format & Encoding

- **Encoding**: Input files must be UTF-8 encoded. Binary or invalid byte sequences trigger defensive rejection.
- **Markdown Support**: Supports CommonMark and GitHub Flavored Markdown (GFM). Exotic or unparseable raw HTML blocks inside Markdown are treated as opaque text nodes.
