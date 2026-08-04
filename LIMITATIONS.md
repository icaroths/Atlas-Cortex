# Atlas Cortex (Evaluation Repository) — Technical Specifications & Limits

This document specifies the operational boundaries and evaluation limits enforced in the **Public Evaluation Repository** (`Atlas-Cortex`).

---

## 1. Node Quota (Evaluation Limit)

- **Quota**: **750 nodes max per document**.
- **Behavior**: The Evaluation environment enforces a hard limit of 750 nodes per parsed document to benchmark public evaluation performance.
- **Truncation Metadata**: When a document exceeds 750 nodes, the AST parser truncates node output to 750 items, cleans dangling edges, and includes the following metadata in the MOC JSON response:
  ```json
  {
    "truncated": true,
    "original_node_count": 1420,
    "truncated_node_count": 750
  }
  ```
- **Enterprise Capacity**: Unrestricted 100% capacity processing is available in the private **Atlas-Cortex_Dev** repository.

---

## 2. Resource Guards

- **File Size (OOM Guard)**: Maximum input file size limit of **50 MB** per document to prevent process memory exhaustion.
- **Subprocess Timeout**: Hard timeout of **30 seconds** per document parse.
- **AST Depth Limit**: Maximum tree depth of **100** levels during AST traversal.
