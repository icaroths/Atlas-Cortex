import copy
import json
import os
from pathlib import Path

import pytest
from atlas_cortex import parse_text

GOLDEN_DIR = Path(os.path.dirname(__file__)) / "golden"

@pytest.mark.parametrize("name", [
    "simple_markdown",
    "nested_lists",
    "code_blocks",
    "tables",
    "frontmatter",
    "mixed_html",
    "unicode",
    "crlf",
    "links_and_anchors",
    "malformed",
])
def test_golden(name):
    input_path = GOLDEN_DIR / f"{name}.md"
    expected_path = GOLDEN_DIR / f"{name}.json"
    
    if not input_path.exists():
        pytest.skip(f"Golden file {name}.md missing")

    input_text = input_path.read_text(encoding="utf-8")
    result = parse_text(input_text)
    
    # Normalizar timestamps/hashes para testes determinísticos
    for n in result.get("nodes", []):
        n["id"] = "mock_id"
    for e in result.get("edges", []):
        e["source"] = "mock_id"
        e["target"] = "mock_id"
        
    result["execution_id"] = "mock_exec"
    result["generated_at"] = "mock_time"
    result["duration_ms"] = 0

    if expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        assert result == expected
    else:
        expected_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        pytest.fail("Golden file created; review and commit.")

def remove_volatile_fields(data):
    d = copy.deepcopy(data)
    d.pop("execution_id", None)
    d.pop("generated_at", None)
    d.pop("duration_ms", None)
    return d

def test_parser_is_deterministic():
    input_path = GOLDEN_DIR / "simple_markdown.md"
    text = input_path.read_text(encoding="utf-8")

    first = parse_text(text)
    second = parse_text(text)

    first_norm = remove_volatile_fields(first)
    second_norm = remove_volatile_fields(second)

    assert first_norm == second_norm
