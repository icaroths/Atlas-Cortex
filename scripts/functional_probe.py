#!/usr/bin/env python3
"""
Atlas Cortex — Functional Probe

Objetivo:
- Testar funcionalidade real do parser.
- Verificar determinismo/idempotência.
- Verificar preservação de conteúdo.
- Verificar comportamento contra inputs hostis.
- Verificar path traversal/symlink, se houver API de arquivo.
- Gerar evidências em functional-probe/.

Este script é uma sondagem black-box.
Ele não substitui auditoria completa, mas revela rapidamente se o comportamento
básico do Atlas Cortex está funcionalmente coerente.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO MANUAL OPCIONAL
# -----------------------------------------------------------------------------
PARSE_TEXT = None
PARSE_FILE = None

# -----------------------------------------------------------------------------
# EVIDÊNCIAS
# -----------------------------------------------------------------------------

EVIDENCE_DIR = Path("functional-probe")
RESULTS = []

VOLATILE_KEYS = {
    "generated_at",
    "timestamp",
    "time",
    "date",
    "duration_ms",
    "duration",
    "elapsed_ms",
    "elapsed",
    "execution_id",
    "run_id",
    "request_id",
    "trace_id",
    "latency_ms",
}


def save_evidence(name: str, content) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / name

    if isinstance(content, bytes):
        path.write_bytes(content)
    elif isinstance(content, str):
        path.write_text(content, encoding="utf-8", errors="replace")
    else:
        path.write_text(
            json.dumps(content, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
            errors="replace",
        )

    return path


def record(name: str, status: str, details: str = "") -> None:
    entry = {
        "name": name,
        "status": status,
        "details": details,
    }
    RESULTS.append(entry)
    print(f"[{status}] {name} :: {details}")


# -----------------------------------------------------------------------------
# UTILITÁRIOS
# -----------------------------------------------------------------------------


def to_jsonable(obj, depth: int = 0):
    if depth > 8:
        return repr(obj)

    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")

    if isinstance(obj, dict):
        return {str(k): to_jsonable(v, depth + 1) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v, depth + 1) for v in obj]

    if hasattr(obj, "model_dump"):
        try:
            return to_jsonable(obj.model_dump(), depth + 1)
        except Exception:
            pass

    if hasattr(obj, "dict"):
        try:
            return to_jsonable(obj.dict(), depth + 1)
        except Exception:
            pass

    if hasattr(obj, "__dict__"):
        try:
            return to_jsonable(vars(obj), depth + 1)
        except Exception:
            pass

    return repr(obj)


def coerce_output(obj):
    obj = to_jsonable(obj)

    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return {"raw": obj}

    if isinstance(obj, dict):
        return obj

    if isinstance(obj, list):
        return {"nodes": obj}

    return {"value": obj}


def strip_volatile(obj):
    if isinstance(obj, dict):
        return {
            k: strip_volatile(v)
            for k, v in obj.items()
            if k not in VOLATILE_KEYS
        }

    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]

    return obj


def canonical(obj) -> str:
    return json.dumps(
        strip_volatile(obj),
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )


def dump_json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def get_nodes(data):
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in ("nodes", "chunks", "sections", "items", "results", "documents"):
        value = data.get(key)
        if isinstance(value, list):
            return value

    return []


def get_edges(data):
    if not isinstance(data, dict):
        return []

    for key in ("edges", "relationships", "links", "relations"):
        value = data.get(key)
        if isinstance(value, list):
            return value

    return []


def get_node_id(node):
    if isinstance(node, dict):
        for key in ("id", "node_id", "uuid", "hash", "content_hash", "sha256"):
            value = node.get(key)
            if value:
                return str(value)
        return None

    if isinstance(node, str):
        return node

    return None


def get_edge_endpoints(edge):
    if not isinstance(edge, dict):
        return None, None

    source = None
    target = None

    for key in ("source", "src", "from", "source_id", "source_node", "source_node_id"):
        if edge.get(key):
            source = str(edge[key])
            break

    for key in ("target", "dst", "to", "target_id", "target_node", "target_node_id"):
        if edge.get(key):
            target = str(edge[key])
            break

    return source, target


def is_adapter_error(exc: Exception) -> bool:
    return str(exc).startswith("Could not call")


def security_like_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    keywords = [
        "traversal",
        "symlink",
        "security",
        "blocked",
        "forbidden",
        "permission",
        "relative",
        "sandbox",
        "outside",
        "invalid path",
        "not allowed",
        "escape",
    ]
    return any(k in msg for k in keywords)


# -----------------------------------------------------------------------------
# DESCOBERTA DA API
# -----------------------------------------------------------------------------


def add_local_paths() -> None:
    candidates = [
        Path.cwd() / "python",
        Path.cwd() / "src",
        Path.cwd() / "atlas_cortex",
    ]
    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))


def import_atlas():
    add_local_paths()

    try:
        return importlib.import_module("atlas_cortex"), None
    except Exception as exc:
        return None, repr(exc)


def discover_parse_text():
    if PARSE_TEXT is not None:
        return PARSE_TEXT, "PARSE_TEXT manual override"

    module, error = import_atlas()
    if module is None:
        return None, f"import atlas_cortex failed: {error}"

    candidates = [
        "parse_text",
        "parse_markdown",
        "parse_string",
        "parse_document_text",
        "parse_content",
        "parse",
    ]

    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn, f"atlas_cortex.{name}"

    submodules = ["core", "parser", "api", "engine", "sdk"]

    for sub in submodules:
        try:
            submodule = importlib.import_module(f"atlas_cortex.{sub}")
        except Exception:
            continue

        for name in candidates:
            fn = getattr(submodule, name, None)
            if callable(fn):
                return fn, f"atlas_cortex.{sub}.{name}"

    return None, "Nenhuma função parse_text encontrada automaticamente."


def discover_parse_file():
    if PARSE_FILE is not None:
        return PARSE_FILE, "PARSE_FILE manual override"

    module, error = import_atlas()
    if module is None:
        return None, f"import atlas_cortex failed: {error}"

    candidates = [
        "parse_file",
        "parse_path",
        "parse_document",
        "parse_document_file",
        "parse_file_secure",
        "parse_secure_file",
    ]

    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn, f"atlas_cortex.{name}"

    submodules = ["core", "parser", "api", "engine", "sdk"]

    for sub in submodules:
        try:
            submodule = importlib.import_module(f"atlas_cortex.{sub}")
        except Exception:
            continue

        for name in candidates:
            fn = getattr(submodule, name, None)
            if callable(fn):
                return fn, f"atlas_cortex.{sub}.{name}"

    return None, "Nenhuma função parse_file encontrada automaticamente."


def call_parse_text(fn, text: str):
    try:
        return fn(text)
    except TypeError as exc:
        attempts = [f"fn(text): {exc}"]

        for kw in ("text", "content", "document", "markdown", "input", "data", "body", "source"):
            try:
                return fn(**{kw: text})
            except TypeError as exc2:
                attempts.append(f"fn({kw}=text): {exc2}")

        try:
            return fn(text, doc_id="functional-probe")
        except TypeError as exc3:
            attempts.append(f"fn(text, doc_id='functional-probe'): {exc3}")

        try:
            return fn(doc_id="functional-probe", text=text)
        except TypeError as exc4:
            attempts.append(f"fn(doc_id='functional-probe', text=text): {exc4}")

        raise RuntimeError(
            "Could not call parse_text. Ajuste PARSE_TEXT no topo do script. "
            "Tentativas: " + " | ".join(attempts)
        )


def call_parse_file(fn, base_dir: Path, user_path: str):
    base_dir = Path(base_dir)
    attempts = []

    positional_attempts = [
        (base_dir, user_path),
        (str(base_dir), user_path),
        (user_path, base_dir),
        (user_path, str(base_dir)),
        (base_dir / user_path,),
        (str(base_dir / user_path),),
    ]

    for args in positional_attempts:
        try:
            return fn(*args), f"args={args!r}"
        except TypeError as exc:
            attempts.append(f"fn{args!r}: {exc}")
        except Exception:
            raise

    keyword_attempts = [
        {"base_dir": base_dir, "user_path": user_path},
        {"base_dir": str(base_dir), "user_path": user_path},
        {"base": base_dir, "path": user_path},
        {"base": str(base_dir), "path": user_path},
        {"base_path": base_dir, "relative_path": user_path},
        {"base_path": str(base_dir), "relative_path": user_path},
        {"path": user_path, "base_dir": base_dir},
        {"file_path": user_path, "base_dir": base_dir},
        {"input_path": user_path, "base_dir": base_dir},
        {"sandbox": base_dir, "path": user_path},
    ]

    for kwargs in keyword_attempts:
        try:
            return fn(**kwargs), f"kwargs={kwargs!r}"
        except TypeError as exc:
            attempts.append(f"fn(**{kwargs!r}): {exc}")
        except Exception:
            raise

    raise RuntimeError(
        "Could not call parse_file. Ajuste PARSE_FILE no topo do script. "
        "Tentativas: " + " | ".join(attempts)
    )


# -----------------------------------------------------------------------------
# TESTES FUNCIONAIS
# -----------------------------------------------------------------------------


def test_discovery():
    parse_text_fn, text_source = discover_parse_text()
    parse_file_fn, file_source = discover_parse_file()

    if parse_text_fn:
        record("discover_parse_text", "PASS", text_source)
    else:
        record("discover_parse_text", "FAIL", text_source)

    if parse_file_fn:
        record("discover_parse_file", "PASS", file_source)
    else:
        record("discover_parse_file", "SKIP", file_source)

    return parse_text_fn, parse_file_fn


def test_simple_parse(parse_text_fn):
    if not parse_text_fn:
        record("simple_parse", "SKIP", "parse_text indisponível")
        return None

    simple = """# Segurança

Este documento descreve regras.

## Autenticação

Use token.
"""

    try:
        out1 = coerce_output(call_parse_text(parse_text_fn, simple))
        save_evidence("simple-output.json", out1)

        nodes = get_nodes(out1)

        if nodes:
            record("simple_parse_returns_nodes", "PASS", f"{len(nodes)} nodes")
        else:
            record("simple_parse_returns_nodes", "FAIL", "Nenhum node retornado")

        ids = [get_node_id(n) for n in nodes]
        if nodes and all(ids):
            record("simple_parse_nodes_have_ids", "PASS", "todos os nodes possuem id")
        else:
            record("simple_parse_nodes_have_ids", "FAIL", "há nodes sem id")

        if isinstance(out1, dict) and out1.get("schema_version") and out1.get("parser_version"):
            record("schema_version_present", "PASS", "schema_version e parser_version presentes")
        else:
            record("schema_version_present", "WARN", "schema_version/parser_version ausentes")

        return out1

    except RuntimeError as exc:
        record("simple_parse", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("simple-parse-exception.txt", traceback.format_exc())
        record("simple_parse", "FAIL", repr(exc))

    return None


def test_determinism(parse_text_fn, first_output):
    if not parse_text_fn:
        record("determinism", "SKIP", "parse_text indisponível")
        return

    if first_output is None:
        record("determinism", "SKIP", "primeiro parse falhou")
        return

    simple = """# Segurança

Este documento descreve regras.

## Autenticação

Use token.
"""

    try:
        out2 = coerce_output(call_parse_text(parse_text_fn, simple))
        save_evidence("determinism-run2.json", out2)
        save_evidence("determinism-run1.json", first_output)

        canon1 = canonical(first_output)
        canon2 = canonical(out2)

        if canon1 == canon2:
            record("determinism_full_output", "PASS", "saídas idênticas após remover campos voláteis")
            return

        nodes1 = get_nodes(first_output)
        nodes2 = get_nodes(out2)

        ids1 = sorted([get_node_id(n) for n in nodes1 if get_node_id(n)])
        ids2 = sorted([get_node_id(n) for n in nodes2 if get_node_id(n)])

        if ids1 and ids1 == ids2:
            record(
                "determinism_full_output",
                "WARN",
                "IDs estáveis, mas output completo difere (ordem/metadados voláteis?)",
            )
        else:
            record("determinism_full_output", "FAIL", "IDs ou output diferem entre execuções")

    except RuntimeError as exc:
        record("determinism", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("determinism-exception.txt", traceback.format_exc())
        record("determinism", "FAIL", repr(exc))


def test_code_preservation(parse_text_fn):
    if not parse_text_fn:
        record("code_preservation", "SKIP", "parse_text indisponível")
        return

    code = """```python
def foo():
    return 1
```
"""

    try:
        out = coerce_output(call_parse_text(parse_text_fn, code))
        save_evidence("code-output.json", out)
        blob = json.dumps(out, ensure_ascii=False, default=str)

        if "    return 1" in blob:
            record("code_indentation_preserved", "PASS", "indentação preservada")
        else:
            record("code_indentation_preserved", "FAIL", "indentação não encontrada")

        if "python" in blob.lower():
            record("code_language_preserved", "PASS", "linguagem python mencionada")
        else:
            record("code_language_preserved", "WARN", "linguagem python não encontrada")

    except RuntimeError as exc:
        record("code_preservation", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("code-preservation-exception.txt", traceback.format_exc())
        record("code_preservation", "FAIL", repr(exc))


def test_table(parse_text_fn):
    if not parse_text_fn:
        record("table_parse", "SKIP", "parse_text indisponível")
        return

    table = """| Nome | Papel |
|---|---|
| Atlas | Parser |
"""

    try:
        out = coerce_output(call_parse_text(parse_text_fn, table))
        save_evidence("table-output.json", out)
        blob = json.dumps(out, ensure_ascii=False, default=str)

        if "Atlas" in blob and "Parser" in blob:
            record("table_content_preserved", "PASS", "conteúdo da tabela preservado")
        else:
            record("table_content_preserved", "FAIL", "conteúdo da tabela perdido")

        if "table" in blob.lower():
            record("table_type_detected", "PASS", "tipo table detectado")
        else:
            record("table_type_detected", "WARN", "tipo table não detectado")

    except RuntimeError as exc:
        record("table_parse", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("table-exception.txt", traceback.format_exc())
        record("table_parse", "FAIL", repr(exc))


def test_unicode_crlf(parse_text_fn):
    if not parse_text_fn:
        record("unicode_crlf", "SKIP", "parse_text indisponível")
        return

    text = "# Título\r\n\r\nConteúdo com ção e 🚀\r\n"

    try:
        out = coerce_output(call_parse_text(parse_text_fn, text))
        save_evidence("unicode-crlf-output.json", out)
        blob = json.dumps(out, ensure_ascii=False, default=str)

        if "ção" in blob and "🚀" in blob:
            record("unicode_preserved", "PASS", "unicode preservado")
        else:
            record("unicode_preserved", "FAIL", "unicode corrompido/perdido")

    except RuntimeError as exc:
        record("unicode_crlf", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("unicode-crlf-exception.txt", traceback.format_exc())
        record("unicode_crlf", "FAIL", repr(exc))


def test_graph_edges(parse_text_fn):
    if not parse_text_fn:
        record("graph_edges", "SKIP", "parse_text indisponível")
        return

    graph_doc = """# A

Veja [B](#b).

## B

Conteúdo B.
"""

    try:
        out = coerce_output(call_parse_text(parse_text_fn, graph_doc))
        save_evidence("graph-output.json", out)
        edges = get_edges(out)

        if not edges:
            record("graph_edges_present", "WARN", "nenhuma aresta retornada")
            return

        degrees = {}
        for edge in edges:
            source, target = get_edge_endpoints(edge)
            if source:
                degrees[source] = degrees.get(source, 0) + 1
            if target:
                degrees[target] = degrees.get(target, 0) + 1

        max_degree = max(degrees.values(), default=0)

        record("graph_edges_present", "PASS", f"{len(edges)} edges")

        if max_degree <= 12:
            record("graph_degree_limited", "PASS", f"grau máximo {max_degree}")
        elif max_degree <= 50:
            record("graph_degree_limited", "WARN", f"grau máximo alto: {max_degree}")
        else:
            record("graph_degree_limited", "FAIL", f"grau máximo explosivo: {max_degree}")

    except RuntimeError as exc:
        record("graph_edges", "FAIL", f"adapter error: {exc}")
    except Exception as exc:
        save_evidence("graph-exception.txt", traceback.format_exc())
        record("graph_edges", "FAIL", repr(exc))


def test_bomb(parse_text_fn, name: str, payload: str):
    if not parse_text_fn:
        record(name, "SKIP", "parse_text indisponível")
        return

    try:
        out = coerce_output(call_parse_text(parse_text_fn, payload))
        save_evidence(f"{name}-output.json", out)

        status = ""
        error = None

        if isinstance(out, dict):
            status = str(out.get("status", "")).lower()
            error = out.get("error")

        if status in {"degraded", "rejected", "error", "failed"} or error:
            record(name, "PASS", f"parser degradou/rejeitou: status={status!r} error={error!r}")
        else:
            record(name, "WARN", "parser retornou sucesso sem status explícito de degradação")

    except RuntimeError as exc:
        if is_adapter_error(exc):
            record(name, "FAIL", f"adapter error: {exc}")
        else:
            save_evidence(f"{name}-exception.txt", traceback.format_exc())
            record(name, "PASS", f"exceção controlada: {exc!r}")

    except Exception as exc:
        save_evidence(f"{name}-exception.txt", traceback.format_exc())
        record(name, "PASS", f"exceção controlada: {exc!r}")


def test_deep_bomb(parse_text_fn):
    payload = ("> " * 30000) + "deep"
    test_bomb(parse_text_fn, "deep_markdown_bomb", payload)


def test_wide_bomb(parse_text_fn):
    payload = "".join(f"- item {i}\n" for i in range(50000))
    test_bomb(parse_text_fn, "wide_markdown_bomb", payload)


def test_timeout(parse_text_fn):
    if not parse_text_fn:
        record("timeout", "SKIP", "parse_text indisponível")
        return

    try:
        sig = inspect.signature(parse_text_fn)
    except Exception:
        record("timeout", "SKIP", "não foi possível inspecionar assinatura para timeout")
        return

    timeout_param = None
    for param_name in sig.parameters:
        if "timeout" in param_name.lower():
            timeout_param = param_name
            break

    if not timeout_param:
        record("timeout", "SKIP", "parse_text não expõe parâmetro de timeout")
        return

    payload = ("> " * 30000) + "timeout"

    try:
        try:
            parse_text_fn(payload, **{timeout_param: 1})
        except TypeError:
            parse_text_fn(text=payload, **{timeout_param: 1})

        record("timeout", "WARN", "parse retornou mesmo com timeout curto")
    except Exception as exc:
        record("timeout", "PASS", f"timeout/erro controlado: {exc!r}")


def test_path_traversal(parse_file_fn):
    if not parse_file_fn:
        record("path_traversal", "SKIP", "parse_file indisponível")
        return

    base = EVIDENCE_DIR / "sandbox"
    base.mkdir(parents=True, exist_ok=True)

    outside = EVIDENCE_DIR / "secret_outside.md"
    outside.write_text("SECRET_OUTSIDE\n", encoding="utf-8")

    malicious = "../secret_outside.md"

    try:
        raw_out, attempt = call_parse_file(parse_file_fn, base, malicious)
        out = coerce_output(raw_out)
        save_evidence("path-traversal-output.json", out)
        blob = json.dumps(out, ensure_ascii=False, default=str)

        if "SECRET_OUTSIDE" in blob:
            record("path_traversal", "FAIL", f"conteúdo externo lido via {attempt}")
        else:
            record(
                "path_traversal",
                "WARN",
                f"chamada succeeded via {attempt}, mas secret não apareceu; validar manualmente",
            )

    except RuntimeError as exc:
        if is_adapter_error(exc):
            record("path_traversal", "FAIL", f"adapter error: {exc}")
        else:
            record("path_traversal", "PASS", f"erro controlado: {exc!r}")

    except Exception as exc:
        save_evidence("path-traversal-exception.txt", traceback.format_exc())
        if security_like_error(exc):
            record("path_traversal", "PASS", f"bloqueio security-like: {exc!r}")
        else:
            record("path_traversal", "WARN", f"erro não claramente security-like: {exc!r}")


def test_symlink(parse_file_fn):
    if not parse_file_fn:
        record("symlink_escape", "SKIP", "parse_file indisponível")
        return

    base = EVIDENCE_DIR / "sandbox"
    base.mkdir(parents=True, exist_ok=True)

    outside = EVIDENCE_DIR / "secret_outside.md"
    outside.write_text("SECRET_OUTSIDE\n", encoding="utf-8")

    link = base / "link.md"

    try:
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(outside, link)
    except OSError as exc:
        record("symlink_escape", "SKIP", f"symlink não suportado/permitido: {exc!r}")
        return

    try:
        raw_out, attempt = call_parse_file(parse_file_fn, base, "link.md")
        out = coerce_output(raw_out)
        save_evidence("symlink-output.json", out)
        blob = json.dumps(out, ensure_ascii=False, default=str)

        if "SECRET_OUTSIDE" in blob:
            record("symlink_escape", "FAIL", f"conteúdo externo lido via symlink {attempt}")
        else:
            record(
                "symlink_escape",
                "WARN",
                f"chamada succeeded via {attempt}, mas secret não apareceu; validar manualmente",
            )

    except RuntimeError as exc:
        if is_adapter_error(exc):
            record("symlink_escape", "FAIL", f"adapter error: {exc}")
        else:
            record("symlink_escape", "PASS", f"erro controlado: {exc!r}")

    except Exception as exc:
        save_evidence("symlink-exception.txt", traceback.format_exc())
        if security_like_error(exc):
            record("symlink_escape", "PASS", f"bloqueio security-like: {exc!r}")
        else:
            record("symlink_escape", "WARN", f"erro não claramente security-like: {exc!r}")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    start = time.time()

    record("probe_started", "PASS", f"evidence dir: {EVIDENCE_DIR.resolve()}")

    parse_text_fn, parse_file_fn = test_discovery()

    first_output = test_simple_parse(parse_text_fn)
    test_determinism(parse_text_fn, first_output)
    test_code_preservation(parse_text_fn)
    test_table(parse_text_fn)
    test_unicode_crlf(parse_text_fn)
    test_graph_edges(parse_text_fn)
    test_deep_bomb(parse_text_fn)
    test_wide_bomb(parse_text_fn)
    test_timeout(parse_text_fn)
    test_path_traversal(parse_file_fn)
    test_symlink(parse_file_fn)

    elapsed_ms = int((time.time() - start) * 1000)

    summary = {
        "pass": sum(1 for r in RESULTS if r["status"] == "PASS"),
        "fail": sum(1 for r in RESULTS if r["status"] == "FAIL"),
        "warn": sum(1 for r in RESULTS if r["status"] == "WARN"),
        "skip": sum(1 for r in RESULTS if r["status"] == "SKIP"),
    }

    report = {
        "project": "Atlas Cortex",
        "probe": "functional_probe",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "platform": platform.platform(),
        "python": sys.version,
        "elapsed_ms": elapsed_ms,
        "summary": summary,
        "results": RESULTS,
    }

    save_evidence("probe-report.json", report)

    print()
    print("=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"Report saved to: {EVIDENCE_DIR / 'probe-report.json'}")

    if summary["fail"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
