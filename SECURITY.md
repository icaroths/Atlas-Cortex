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

## Known Vulnerabilities & Accepted Risks

- **pyo3 v0.21.2**: 
  - `RUSTSEC-2025-0020`: Risk of buffer overflow in `PyString::from_object`.
  - `RUSTSEC-2026-0177`: Missing `Sync` bound on `PyCFunction::new_closure` closures.
  - **Justificativa (Accepted Risk)**: A versão 0.22.6+ quebra a macro `pymodule` do nosso build atual (engine). Optamos pelo *version pinning* na versão 0.21.2 e as vulnerabilidades acima foram aceitas e ignoradas nas ferramentas de CI/CD (`cargo audit --ignore`) até que o código em Rust seja refatorado de forma segura para suportar a versão `pyo3 >=0.29.0`. A execução do ambiente de produção e de validações ocorre sem uso inseguro dessas APIs especificamente vulneráveis de strings e closures não mapeadas.
