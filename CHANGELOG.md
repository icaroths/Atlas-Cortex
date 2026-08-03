# Changelog

All notable changes to the Atlas Cortex project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0-enterprise] - 2026-08-03

### Added
- **AST Native Engine**: High-performance Rust parser using Tree-Sitter MD.
- **MOC Metadata**: Added `truncated`, `original_node_count`, and `truncated_node_count` fields to MOC JSON schema.
- **Unit Tests**: Full unit test coverage in Rust (`cargo test`) and Python (`pytest`).
- **CI/CD & Auto-Merge**: GitHub Actions pipeline (`ci.yml`) and automated PR merge workflow (`auto-merge.yml`).
- **Security & Governance**: Technical limitations guide (`LIMITATIONS.md`), Security policy (`SECURITY.md`), Cargo Deny rules, and SBOM generation script.

### Changed
- Re-architected parser pipeline from regex-based splitting to deterministic AST graph generation.
- Enforced 50MB file size OOM guard and 30s execution timeout.
