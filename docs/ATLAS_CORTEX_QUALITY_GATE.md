# Atlas Cortex — Padrão Oficial de Auditoria, Qualidade, Segurança e Entrega

Este documento define o padrão obrigatório para:

- correções de bugs;
- novas implementações;
- auditorias de segurança;
- validação de benchmarks;
- releases;
- manutenção contínua do projeto.

Ele existe para impedir regressões, overclaims e falsas sensações de prontidão.

A regra central é:

> **Alegação sem evidência não é aceita como verdade de engenharia.**

---

## 1. Objetivo

Estabelecer um processo repetível, auditável e objetivo para garantir que o Atlas Cortex permaneça:

- determinístico;
- seguro;
- funcional;
- performático;
- reproduzível;
- auditável;
- pronto para evolução contínua.

Este documento deve ser usado como referência antes de qualquer:

- commit relevante;
- pull request;
- release;
- alteração em parser;
- alteração em grafo;
- alteração em benchmark;
- alteração em integração Python/LangChain;
- alteração em infraestrutura ou CI.

---

## 2. Princípios inegociáveis

### 2.1. Evidência acima de discurso

Nenhum item é considerado resolvido apenas por mensagem de commit ou declaração verbal.

É necessário apresentar:

- log de comando;
- teste automatizado;
- artefato regenerado;
- diff verificável;
- saída de auditoria;
- scorecard preenchido.

---

### 2.2. Determinismo e idempotência

O sistema deve produzir resultados estáveis para o mesmo input.

Isso significa que:

- mesmos arquivos devem gerar mesmos nós;
- mesmos nós devem gerar mesmos IDs;
- mesmas arestas devem gerar mesmos IDs;
- re-execuções não devem criar duplicatas;
- re-ingestões devem permitir reconciliação.

---

### 2.3. Fail closed

Em caso de falha, o sistema deve falhar de forma segura.

Exemplos:

- juiz LLM indisponível deve reprovar, não aprovar;
- parser com input inválido deve retornar erro tratável;
- timeout deve abortar a operação;
- path traversal deve bloquear;
- symlink escape deve bloquear;
- binário ausente deve gerar erro claro.

---

### 2.4. Menor superfície de ataque

Evitar:

- `shell=True`;
- `os.system`;
- execução de binário por PATH não confiável;
- logs com conteúdo sensível;
- temporários previsíveis;
- entrada não validada;
- dependências não auditadas.

---

### 2.5. Reprodutibilidade

Benchmarks, testes e builds devem ser reproduzíveis.

Isso exige:

- versões fixadas;
- lockfiles;
- seeds;
- artefatos commitados;
- CI com verificação de drift;
- documentação de ambiente.

---

### 2.6. Observabilidade

Produção sem observabilidade é caixa preta.

O sistema deve permitir responder:

- o que falhou?
- onde falhou?
- por quê?
- quanto tempo levou?
- quanto recurso consumiu?
- qual documento causou o problema?

---

## 3. Fluxo padrão para qualquer correção ou nova implementação

Toda mudança relevante deve seguir o fluxo abaixo.

---

### Fase 1 — Diagnóstico

Antes de modificar código:

1. identificar o problema;
2. classificar severidade;
3. reproduzir o problema;
4. salvar evidências iniciais;
5. definir critério de aceite.

Saída esperada:

```text
problema:
severidade:
evidência:
critério de aceite:
```

---

### Fase 2 — Extração de realidade

Rodar auditoria sem alterar código.

Objetivo:

- medir estado atual;
- evitar viés;
- gerar scorecard real.

Itens mínimos:

```text
cargo fmt --check
cargo clippy
cargo test
cargo audit
pytest
pip-audit
bandit
benchmark drift
git hygiene
```

---

### Fase 3 — Remediação

Corrigir apenas o que foi reprovado.

Regras:

- não introduzir gambiarras;
- não silenciar lints sem justificativa;
- não corrigir só o sintoma;
- adicionar teste para o bug corrigido;
- atualizar documentação se o comportamento mudou.

---

### Fase 4 — Revalidação

Rodar novamente todos os testes relevantes.

Saída esperada:

```text
antes: FAIL
depois: PASS
evidência: audit-evidence/...
```

---

## 4. Portões de qualidade

O projeto usa três níveis de criticidade.

---

## 4.1. P0 — Bloqueantes

Itens P0 impedem release.

Se qualquer P0 falhar:

```text
RELEASE BLOCKED
```

Exemplos:

- `engine/target` versionado;
- `.gitignore` inválido;
- `cargo test` falhando;
- `cargo clippy -D warnings` falhando;
- `cargo audit` com vulnerabilidade crítica;
- `pytest` falhando;
- `shell=True` em código relevante;
- juiz LLM stub;
- benchmark dessincronizado;
- path traversal não bloqueado;
- parser crashando com input malicioso;
- IDs não determinísticos;
- timeout inexistente em operação externa.

---

## 4.2. P1 — Alto risco

Itens P1 não devem ser ignorados em release estável.

Meta para release v1.0:

```text
P1 >= 90% PASS
```

Exemplos:

- golden tests incompletos;
- reconciliação de grafo ausente;
- limites de DoS incompletos;
- schema não versionado;
- benchmark sem estatística;
- logs com dados sensíveis;
- ausência de testes de timeout;
- ausência de testes de symlink;
- ausência de testes de Unicode/CRLF;
- ausência de métricas de grafo.

---

## 4.3. P2 — Maturidade enterprise

Itens P2 são necessários para adoção enterprise robusta.

Meta para enterprise-ready:

```text
P2 >= 70% PASS
```

Exemplos:

- empacotamento pip com wheels;
- observabilidade completa;
- threat model documentado;
- SECURITY.md;
- CHANGELOG.md;
- SBOM;
- releases assinados;
- telemetria;
- health checks;
- suporte multiplataforma;
- documentação operacional.

---

# 5. Checklist permanente para qualquer PR

Todo pull request deve responder:

## 5.1. Qualidade básica

```text
[ ] Testes passam localmente
[ ] Testes passam no CI
[ ] Nenhum warning novo introduzido
[ ] Nenhum lint silenciado sem justificativa
[ ] Código formatado
[ ] Documentação atualizada
[ ] Changelog atualizado, se aplicável
```

---

## 5.2. Segurança

```text
[ ] Nenhuma chamada shell insegura
[ ] Nenhum path traversal possível
[ ] Nenhum symlink escape possível
[ ] Nenhum input malicioso causa crash
[ ] Nenhum segredo commitado
[ ] Nenhum log com conteúdo sensível
[ ] Nenhuma dependência vulnerável conhecida
```

---

## 5.3. Funcionalidade

```text
[ ] Comportamento antigo não regrediu
[ ] Novos testes adicionados
[ ] Golden tests atualizados, se aplicável
[ ] Saída continua determinística
[ ] Schema versionado, se aplicável
[ ] Metadados preservados
```

---

## 5.4. Benchmarks

```text
[ ] Benchmark regenerado se lógica mudou
[ ] JSON de resultado commitado
[ ] Metodologia declarada bate com o código
[ ] Não há stub no lugar de teste real
[ ] Drift check passa
```

---

## 5.5. Grafo

```text
[ ] IDs de nós determinísticos
[ ] IDs de arestas determinísticos
[ ] Grau máximo respeitado
[ ] Arestas têm proveniência
[ ] Reconciliação testada
[ ] Métricas de grafo não degradaram
```

---

# 6. Checklist de auditoria estática

Este bloco deve ser executado em toda auditoria completa.

---

## 6.1. Preparação

```bash
mkdir -p audit-evidence
git rev-parse HEAD > audit-evidence/commit.txt
date > audit-evidence/date.txt
uname -a > audit-evidence/uname.txt || true
python --version > audit-evidence/python-version.txt
cargo --version > audit-evidence/cargo-version.txt
rustc --version > audit-evidence/rustc-version.txt
```

---

## 6.2. Higiene de repositório

```bash
git ls-files engine/target > audit-evidence/git-ls-files-target.txt
file .gitignore > audit-evidence/gitignore-encoding.txt
du -sh .git > audit-evidence/git-size.txt
```

### Critério

- `git ls-files engine/target` deve retornar vazio;
- `.gitignore` deve ser UTF-8 ou ASCII;
- `.git` não deve estar inchado por binários.

---

## 6.3. Rust

```bash
cd engine

cargo fmt --check > ../audit-evidence/cargo-fmt.txt 2>&1
cargo clippy --all-targets --all-features -- -D warnings > ../audit-evidence/cargo-clippy.txt 2>&1
cargo test --release > ../audit-evidence/cargo-test.txt 2>&1

cargo audit > ../audit-evidence/cargo-audit.txt 2>&1 || true
cargo deny check bans licenses sources > ../audit-evidence/cargo-deny.txt 2>&1 || true

cd ..
```

### Critério

- `cargo fmt --check`: exit code 0;
- `cargo clippy -D warnings`: exit code 0;
- `cargo test`: exit code 0;
- `cargo audit`: exit code 0;
- `cargo deny`: sem violações críticas.

---

## 6.4. Python

```bash
python -m venv .venv-audit
source .venv-audit/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-dev.txt || pip install pytest ruff mypy pip-audit bandit

ruff check . > audit-evidence/ruff.txt 2>&1
mypy . > audit-evidence/mypy.txt 2>&1
pytest -q > audit-evidence/pytest.txt 2>&1
pip-audit > audit-evidence/pip-audit.txt 2>&1
bandit -r python -ll > audit-evidence/bandit.txt 2>&1 || true
bandit -r scripts -ll > audit-evidence/bandit-scripts.txt 2>&1 || true
```

### Critério

- `ruff`: exit code 0;
- `mypy`: exit code 0 ou exceções justificadas;
- `pytest`: exit code 0;
- `pip-audit`: exit code 0;
- `bandit`: sem findings altos/médios relevantes.

---

## 6.5. Segurança por grep

```bash
grep -RInE "shell\s*=\s*True" python scripts > audit-evidence/grep-shell-true.txt || true
grep -RIn "os.system" python scripts > audit-evidence/grep-os-system.txt || true
grep -RInE "eval\(|exec\(" python scripts > audit-evidence/grep-eval-exec.txt || true
grep -RIn "subprocess" python scripts > audit-evidence/grep-subprocess.txt || true
```

### Critério

- nenhum `shell=True` relevante;
- nenhum `os.system`;
- nenhum `eval`/`exec` sem justificativa;
- todo `subprocess` deve usar lista de argumentos e timeout.

---

# 7. Checklist de segurança obrigatório

---

## 7.1. Path traversal

O sistema deve validar caminhos contra um diretório base.

Padrão recomendado:

```python
from pathlib import Path

def validate_path(base_dir: Path, user_path: str) -> Path:
    base = base_dir.resolve()
    candidate = (base / user_path).resolve()

    if not candidate.is_relative_to(base):
        raise SecurityError("Path traversal or symlink escape blocked")

    return candidate
```

### Testes obrigatórios

```text
../secret.txt
foo/../../secret.txt
..\\secret.txt
symlink para fora do sandbox
symlink relativo
UNC path no Windows
drive letter diferente no Windows
null bytes
unicode normalization
caminho longo
```

### Critério

Toda tentativa de escape deve falhar com erro tratável.

---

## 7.2. Subprocess seguro

É proibido:

```python
subprocess.run(f"comando {arg}", shell=True)
os.system(f"comando {arg}")
```

Padrão aceito:

```python
subprocess.run(
    [binary_path, "parse", file_path],
    capture_output=True,
    timeout=30,
    check=False,
)
```

### Requisitos

- lista de argumentos;
- timeout explícito;
- binário com caminho confiável;
- tratamento de exit code;
- tratamento de stderr;
- limpeza de recursos;
- kill/cancelamento quando possível.

---

## 7.3. Limites contra DoS

O parser deve possuir limites configuráveis.

Recomendado:

```text
max_file_bytes
max_ast_depth
max_sibling_nodes
max_total_nodes
max_total_edges
max_line_length
max_code_block_bytes
max_table_rows
max_parse_duration
max_concurrent_parses
```

### Testes obrigatórios

```text
deep_nested.md
huge_list.md
huge_table.md
huge_line.md
many_small_nodes.md
invalid_utf8.md
null_bytes.md
crlf_bom.md
mixed_html.md
malformed.md
```

### Critério

O sistema deve:

```text
reject
degrade
timeout
safe_error
```

Nunca:

```text
panic
segfault
hang
OOM
silent corruption
```

---

## 7.4. Timeout real

Timeout não pode ser apenas decorativo.

### Requisitos

- timeout configurável;
- subprocesso cancelado ou morto;
- temporários limpos;
- erro tratável;
- métrica de timeout emitida;
- log sem conteúdo sensível.

---

## 7.5. Arquivos temporários

Recomendado:

```python
import tempfile

with tempfile.TemporaryDirectory(prefix="atlas_") as tmpdir:
    ...
```

### Requisitos

- nomes aleatórios;
- permissões restritas;
- cleanup automático;
- quota de disco;
- rotina de faxina para crash duro;
- não usar `/tmp` com nome fixo.

---

## 7.6. Logs e privacidade

Logs padrão não devem conter:

```text
conteúdo completo de documentos
queries completas
contextos completos
chaves
tokens
segredos
dados pessoais
```

Logs devem conter:

```text
doc_id
content_hash
node_count
edge_count
duration_ms
error_code
parser_version
schema_version
```

Debug de conteúdo deve ser:

- explícito;
- desligado por padrão;
- documentado como inseguro.

---

## 7.7. Supply chain

### Rust

```bash
cargo audit
cargo deny check bans licenses sources
```

### Python

```bash
pip-audit
```

### Node

```bash
npm ci
npm audit --audit-level=high
```

### Modelos

Requisitos:

- revisão fixada;
- hash verificado quando possível;
- preferência por safetensors;
- cache local/offline em produção;
- licença verificada.

---

# 8. Checklist funcional obrigatório

---

## 8.1. Golden tests

Todo parser deve ter golden tests.

Casos mínimos:

```text
simple_markdown.md
nested_lists.md
code_blocks.md
tables.md
frontmatter.md
mixed_html.md
unicode.md
crlf.md
links_and_anchors.md
malformed.md
```

### Critério

A saída deve ser estável e revisada.

Golden tests não podem ser gerados cegamente sem revisão humana.

---

## 8.2. Preservação de informação

O parser não pode destruir semântica.

### Deve preservar

- indentação de código;
- quebras de linha;
- linguagem de code block;
- estrutura de tabelas;
- links;
- âncoras;
- headings;
- frontmatter;
- metadados estruturais.

### Recomendado

Cada nó deve conter:

```json
{
  "id": "sha256...",
  "type": "paragraph|heading|code_block|table|list_item",
  "content": "...",
  "raw_content": "...",
  "heading_path": [],
  "byte_offset_start": 0,
  "byte_offset_end": 0,
  "content_hash": "sha256...",
  "parser_version": "1.0.0",
  "schema_version": "1.0.0"
}
```

---

## 8.3. Determinismo

Teste obrigatório:

```python
def test_parser_is_deterministic():
    text = read_input()

    first = parse_text(text)
    second = parse_text(text)

    first = remove_volatile_fields(first)
    second = remove_volatile_fields(second)

    assert first == second
```

### Campos voláteis permitidos

```text
generated_at
execution_id
duration_ms
```

### Campos que nunca podem mudar

```text
node.id
edge.id
node.content_hash
edge.source
edge.target
edge.type
```

---

## 8.4. Schema versionado

Toda saída estruturada deve declarar:

```json
{
  "schema_version": "1.0.0",
  "parser_version": "1.0.0"
}
```

### Regra

Se a saída muda de forma incompatível:

- bump de versão;
- changelog;
- migração documentada;
- testes de compatibilidade.

---

# 9. Checklist de GraphRAG obrigatório

---

## 9.1. IDs determinísticos

IDs devem ser derivados de hash estável.

Exemplo:

```text
node_id = sha256(
  doc_id
  + structural_path
  + node_type
  + normalized_content
  + schema_version
  + parser_version
)
```

---

## 9.2. Edge IDs determinísticos

Arestas também devem ter ID estável.

Exemplo:

```text
edge_id = sha256(
  source_node_id
  + target_node_id
  + edge_type
  + edge_method
  + provenance
)
```

---

## 9.3. Controle de densidade

Toda geração de arestas deve ter:

```text
max_edges_per_node
edge_score_threshold
candidate_generation_limit
knn_limit
deduplication
```

### Critério

Grafo não pode explodir em O(N²) sem controle.

---

## 9.4. Proveniência de arestas

Cada aresta deve declarar:

```json
{
  "source": "...",
  "target": "...",
  "type": "reference|semantic|cooccurrence|hierarchy",
  "weight": 0.91,
  "method": "anchor_map|embedding_cosine|entity_overlap",
  "provenance": "doc_id",
  "schema_version": "1.0.0"
}
```

---

## 9.5. Reconciliação

Re-ingestão deve suportar:

```text
upsert de nós novos
update de nós alterados
delete de nós removidos
delete de arestas órfãs
versionamento de documento
manifest de ingestão
```

### Teste obrigatório

```text
1. ingerir documento v1
2. salvar manifest v1
3. modificar documento para v2
4. ingerir documento v2
5. comparar manifests
6. validar remoção/atualização
```

---

## 9.6. Métricas de grafo

Toda mudança em lógica de grafo deve reportar:

```text
node_count
edge_count
avg_degree
max_degree
orphan_nodes
connected_components
density
edge_type_distribution
```

---

# 10. Checklist de benchmark obrigatório

---

## 10.1. Regra de ouro

Se a lógica de parsing, chunking, embedding ou grafo mudou:

```text
benchmark deve ser reexecutado
artefato deve ser regenerado
diff deve ser commitado
```

---

## 10.2. Itens obrigatórios

```text
[ ] corpus correto
[ ] metodologia correta
[ ] modelo de embedding declarado
[ ] versão do modelo declarada
[ ] seed declarada
[ ] juiz declarado
[ ] judge real, não stub
[ ] judge falha fechado
[ ] saída JSON validada
[ ] artefato sincronizado
[ ] drift check passa
```

---

## 10.3. Juiz LLM

É proibido usar stub que sempre aprova.

Exemplo proibido:

```python
def run_ollama_judge(query, context):
    return len(context) > 100
```

### Requisitos

- chamada real;
- timeout;
- validação de saída;
- schema estrito;
- falha fechada;
- prompt com contexto delimitado;
- logs de auditoria.

---

## 10.4. Qualidade estatística

Benchmarks maduros devem reportar:

```json
{
  "mean": 0.0,
  "std": 0.0,
  "min": 0.0,
  "max": 0.0,
  "samples": 0,
  "seed": 42
}
```

---

## 10.5. Baselines

Sempre que possível comparar com:

```text
RecursiveCharacterTextSplitter
fixed-size chunks
semantic chunks
parent-child chunks
hierarchical retrieval
reranking
```

---

# 11. Checklist de performance

---

## 11.1. Métricas mínimas

Toda mudança relevante deve medir:

```text
parse latency p50
parse latency p95
parse latency p99
memory peak
CPU usage
node throughput
edge throughput
temp disk usage
error rate
timeout rate
```

---

## 11.2. Concorrência

Requisitos:

- semaphore ou limite de tarefas;
- backpressure;
- cancelamento;
- fila observável;
- timeout por tarefa;
- limpeza de recursos.

---

## 11.3. Testes de carga mínimos

Cenários:

```text
1 arquivo grande
10 arquivos médios
100 arquivos pequenos
50 requisições concorrentes
30 minutos de carga sustentada
```

---

# 12. Checklist de observabilidade

---

## 12.1. Logs estruturados

Exemplo:

```json
{
  "event": "parse_completed",
  "doc_id": "...",
  "content_hash": "...",
  "node_count": 42,
  "edge_count": 17,
  "duration_ms": 120,
  "fallback_used": false,
  "parser_version": "1.0.0",
  "schema_version": "1.0.0"
}
```

---

## 12.2. Métricas recomendadas

```text
atlas_parse_duration_seconds
atlas_nodes_total
atlas_edges_total
atlas_parse_errors_total
atlas_timeout_total
atlas_fallback_total
atlas_memory_usage_bytes
atlas_queue_depth
```

---

## 12.3. Health checks

O sistema deve verificar:

```text
binário Rust disponível
Python dependencies disponíveis
Ollama disponível, se necessário
disco com espaço
diretório temporário gravável
permissões corretas
```

---

# 13. Checklist de empacotamento

---

## 13.1. Instalação

O projeto deve tender para:

```bash
pip install atlas-cortex
```

sem exigir Rust instalado.

---

## 13.2. Requisitos

```text
pyproject.toml
maturin ou mecanismo equivalente
wheels multiplataforma
versionamento semântico
changelog
validação de binário
```

---

## 13.3. Plataformas alvo

```text
Linux x86_64
Linux ARM64
macOS Intel
macOS Apple Silicon
Windows
```

---

# 14. Checklist de governança

---

## 14.1. Documentos obrigatórios

```text
README.md
LICENSE
SECURITY.md
CHANGELOG.md
docs/threat-model.md
docs/operations.md
docs/benchmarks.md
docs/ATLAS_CORTEX_QUALITY_GATE.md
```

---

## 14.2. Política de segurança

O projeto deve possuir:

```text
canal de reporte de vulnerabilidade
política de divulgação
tempo de resposta esperado
classificação de severidade
processo de patch
```

---

## 14.3. Política de release

Toda release deve ter:

```text
tag
changelog
hash do commit
artefatos assinados ou verificáveis
notas de breaking changes
migrações documentadas
```

---

# 15. Regras para uso de `allow`, `ignore` e supressões

---

## 15.1. Rust

Evitar:

```rust
#[allow(clippy::...)]
```

sem justificativa.

Se necessário:

```rust
// REASON: explicar por que o lint é seguro aqui.
// TICKET: #123
#[allow(clippy::collapsible_if)]
```

---

## 15.2. Python

Evitar:

```python
# type: ignore
# noqa
```

sem justificativa.

Se necessário:

```python
# REASON: explicar motivo
# TICKET: #123
```

---

# 16. Anti-padrões proibidos

Os padrões abaixo são proibidos sem exceção documentada.

---

## 16.1. Commitar build artifacts

Proibido:

```text
engine/target/
node_modules/
__pycache__/
*.pdb
*.exe
*.so
*.rlib
```

---

## 16.2. Stub disfarçado de teste real

Proibido:

```python
return len(context) > 100
```

como juiz LLM.

---

## 16.3. Benchmark com metodologia errada

Proibido declarar:

```text
TF-IDF
```

quando o código usa embeddings.

---

## 16.4. Correção apenas na mensagem do commit

Proibido dizer:

```text
fix: remove target
```

se o alvo continua rastreado.

---

## 16.5. Código corrigido, artefato não regenerado

Se o script muda, o JSON de benchmark deve ser regenerado.

---

## 16.6. Teste que não pode falhar

Teste que sempre passa não é teste.

---

## 16.7. Logs com conteúdo bruto

Proibido logar conteúdo completo por padrão.

---

## 16.8. Shell inseguro

Proibido:

```python
shell=True
os.system
popen inseguro
```

---

# 17. Definition of Ready

Uma tarefa só deve começar quando tiver:

```text
[ ] problema claramente descrito
[ ] severidade classificada
[ ] critério de aceite definido
[ ] testes planejados
[ ] riscos identificados
[ ] áreas impactadas mapeadas
[ ] evidências iniciais salvas
```

---

# 18. Definition of Done

Uma tarefa só está concluída quando:

```text
[ ] código implementado
[ ] testes adicionados
[ ] testes passando
[ ] lint passando
[ ] formatação passando
[ ] documentação atualizada
[ ] changelog atualizado
[ ] artefatos regenerados
[ ] evidências salvas
[ ] scorecard atualizado
[ ] nenhum P0 novo introduzido
[ ] nenhum regressão conhecida
```

---

# 19. Scorecard padrão

Usar este modelo em toda auditoria.

---

## 19.1. P0

| ID | Item | Status | Evidência |
|---|---|---|---|
| P0-01 | `engine/target` fora do Git | PASS/FAIL | git-ls-files-target.txt |
| P0-02 | `.gitignore` UTF-8 válido | PASS/FAIL | gitignore-encoding.txt |
| P0-03 | Histórico sem binários gigantes | PASS/FAIL | git-size.txt |
| P0-04 | `cargo fmt --check` | PASS/FAIL | cargo-fmt.txt |
| P0-05 | `cargo clippy -D warnings` | PASS/FAIL | cargo-clippy.txt |
| P0-06 | `cargo test` | PASS/FAIL | cargo-test.txt |
| P0-07 | `cargo audit` | PASS/FAIL | cargo-audit.txt |
| P0-08 | `pytest` | PASS/FAIL | pytest.txt |
| P0-09 | `pip-audit` | PASS/FAIL | pip-audit.txt |
| P0-10 | Sem `shell=True` | PASS/FAIL | grep-shell-true.txt |
| P0-11 | Sem `os.system` | PASS/FAIL | grep-os-system.txt |
| P0-12 | Subprocess com timeout | PASS/FAIL | grep-subprocess.txt |
| P0-13 | Juiz LLM real | PASS/FAIL | bench-quality-run.txt |
| P0-14 | Juiz falha fechado | PASS/FAIL | judge-fail-closed.txt |
| P0-15 | Benchmark sem drift | PASS/FAIL | bench-drift.txt |
| P0-16 | Metodologia correta | PASS/FAIL | methodology-check.txt |
| P0-17 | Parser determinístico | PASS/FAIL | idempotency-diff.txt |
| P0-18 | Limites de DoS | PASS/FAIL | dos-tests.txt |
| P0-19 | Path traversal bloqueado | PASS/FAIL | test-security.txt |
| P0-20 | Symlink escape bloqueado | PASS/FAIL | test-security.txt |

---

## 19.2. P1

| ID | Item | Status | Evidência |
|---|---|---|---|
| P1-01 | Golden tests completos | PASS/FAIL | golden-tests.txt |
| P1-02 | Preservação de conteúdo | PASS/FAIL | golden-tests.txt |
| P1-03 | Schema versionado | PASS/FAIL | schema-version.txt |
| P1-04 | Grafo com grau máximo | PASS/FAIL | graph-metrics.txt |
| P1-05 | Arestas com proveniência | PASS/FAIL | graph-schema.txt |
| P1-06 | Métricas de grafo | PASS/FAIL | graph-metrics.txt |
| P1-07 | Benchmark com seed | PASS/FAIL | benchmark-json |
| P1-08 | Benchmark com estatística | PASS/FAIL | benchmark-json |
| P1-09 | Baselines | PASS/FAIL | benchmark-report |
| P1-10 | Reconciliação de grafo | PASS/FAIL | reconciliation-test.txt |
| P1-11 | Timeout de parsing | PASS/FAIL | timeout-test.txt |
| P1-12 | Limite de nós | PASS/FAIL | dos-tests.txt |
| P1-13 | Limite de concorrência | PASS/FAIL | load-test.txt |
| P1-14 | Cleanup de temporários | PASS/FAIL | temp-test.txt |
| P1-15 | Logs sem dados sensíveis | PASS/FAIL | log-review.txt |

---

## 19.3. P2

| ID | Item | Status | Evidência |
|---|---|---|---|
| P2-01 | Observabilidade | PASS/FAIL | tracing-logs |
| P2-02 | Métricas operacionais | PASS/FAIL | metrics.txt |
| P2-03 | Health checks | PASS/FAIL | health.txt |
| P2-04 | Empacotamento pip | PASS/FAIL | packaging.txt |
| P2-05 | Wheels multiplataforma | PASS/FAIL | wheels.txt |
| P2-06 | SECURITY.md | PASS/FAIL | file-exists |
| P2-07 | CHANGELOG.md | PASS/FAIL | file-exists |
| P2-08 | Threat model | PASS/FAIL | file-exists |
| P2-09 | SBOM | PASS/FAIL | sbom.txt |
| P2-10 | Release assinado | PASS/FAIL | release-notes |

---

# 20. Critérios de release

---

## 20.1. Release experimental

Permitida se:

```text
P0 críticos de segurança: 100% PASS
P0 geral: >= 80%
P1: >= 60%
```

---

## 20.2. Release estável v1.0

Permitida se:

```text
P0: 100% PASS
P1: >= 90%
P2: >= 40%
```

---

## 20.3. Enterprise-ready

Permitida se:

```text
P0: 100% PASS
P1: >= 95%
P2: >= 70%
threat model documentado
testes de carga documentados
política de segurança documentada
observabilidade funcional
empacotamento maduro
```

---

# 21. Rotina de manutenção contínua

---

## 21.1. A cada PR

```text
rodar testes
rodar lint
verificar drift
verificar segurança básica
atualizar docs
```

---

## 21.2. A cada release

```text
auditoria completa
cargo audit
pip-audit
npm audit
benchmark regenerado
changelog
tag
evidências
```

---

## 21.3. Mensalmente

```text
revisar dependências
revisar alertas de segurança
revisar golden tests
revisar threat model
revisar benchmarks
revisar performance
revisar logs e métricas
```

---

# 22. Template de evidência final

Toda auditoria deve salvar:

```text
audit-evidence/
  commit.txt
  date.txt
  uname.txt
  python-version.txt
  cargo-version.txt
  rustc-version.txt
  git-ls-files-target.txt
  gitignore-encoding.txt
  git-size.txt
  cargo-fmt.txt
  cargo-clippy.txt
  cargo-test.txt
  cargo-audit.txt
  cargo-deny.txt
  ruff.txt
  mypy.txt
  pytest.txt
  pip-audit.txt
  bandit.txt
  grep-shell-true.txt
  grep-os-system.txt
  grep-eval-exec.txt
  grep-subprocess.txt
  golden-tests.txt
  security-tests.txt
  idempotency-diff.txt
  reconciliation-test.txt
  bench-tokens-run.txt
  bench-quality-run.txt
  bench-drift.txt
  graph-metrics.txt
  load-test.txt
```

E gerar hash:

```bash
sha256sum audit-evidence/* > audit-evidence.sha256
```

---

# 23. Template de parecer final

```text
Projeto: Atlas Cortex
Commit auditado: <hash>
Data: <data>

P0: X/Y PASS
P1: X/Y PASS
P2: X/Y PASS

Bloqueios críticos:
- ...

Riscos altos:
- ...

Riscos médios:
- ...

Classificação:
( ) release blocked
( ) experimental release
( ) stable v1.0 candidate
( ) production-ready
( ) enterprise-ready

Nota final: <nota>
```

---

# 24. Regra final

O Atlas Cortex só deve ser declarado pronto para um nível quando as evidências sustentarem esse nível.

Níveis:

```text
experimental: funciona, mas com riscos conhecidos
stable: confiável para uso geral
production-ready: seguro, observável e auditável
enterprise-ready: production-ready + governança + suporte + compliance
```

A declaração correta deve ser sempre:

> “O projeto está no nível X porque os itens Y foram verificados com evidência Z.”

Nunca:

> “O projeto está pronto porque acreditamos que está pronto.”
