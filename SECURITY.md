# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within Atlas Cortex, please send an email to the maintainers or open a confidential security advisory on GitHub.

### Security Guarantees & Built-in Defenses

1. **Memory Safety**: Core AST parser written in safe Rust.
2. **Resource Exhaustion Defenses**:
   - Max file size limit: 50MB
   - Max AST traversal depth: 100
   - Execution timeout: 30s
3. **No Shell Execution**: Subprocess execution strictly uses direct argument vectors without shell evaluation (`shell=False`).
