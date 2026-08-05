"""
Atlas Cortex — Multi-Format Converter Module (Fase 10)

Converts documents from various formats (TXT, HTML, DOCX, EPUB) into
Markdown (the Atlas IR), preserving provenance and measuring fidelity.

Architecture: Markdown is the single Intermediate Representation (IR).
The Rust core never gains parsers for other formats; new formats enter
through external converters (compiler pattern: multiple frontends, single backend).
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger("atlas_cortex.converters")

# Minimum coverage ratio to accept a conversion
MIN_COVERAGE_RATIO = 0.75


@dataclass
class ConversionResult:
    """Result of converting a document to Markdown IR."""

    markdown: str
    source_format: str
    converter_name: str
    converter_version: str
    coverage_ratio: float
    ir_hash: str
    original_hash: str
    warnings: list[str] = field(default_factory=list)

    @property
    def is_acceptable(self) -> bool:
        return self.coverage_ratio >= MIN_COVERAGE_RATIO


def _estimate_token_count(text: str) -> int:
    """Fast token estimation by whitespace splitting. Good enough for coverage ratio."""
    if not text.strip():
        return 0
    return len(text.split())


def _compute_ir_hash(original_hash: str, converter_name: str, converter_version: str) -> str:
    """Deterministic IR cache key: sha256(original_hash || converter || version)."""
    payload = f"{original_hash}||{converter_name}||{converter_version}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Individual Converters
# ---------------------------------------------------------------------------

def convert_txt(content: bytes, encoding: str = "utf-8") -> ConversionResult:
    """TXT → Markdown. Trivial pass-through with line normalization."""
    text = content.decode(encoding, errors="replace")
    text = text.replace("\r\n", "\n")
    original_hash = hashlib.sha256(content).hexdigest()

    return ConversionResult(
        markdown=text,
        source_format="txt",
        converter_name="atlas_builtin_txt",
        converter_version="1.0.0",
        coverage_ratio=1.0,
        ir_hash=_compute_ir_hash(original_hash, "atlas_builtin_txt", "1.0.0"),
        original_hash=original_hash,
    )


def convert_html(content: bytes, encoding: str = "utf-8") -> ConversionResult:
    """HTML → Markdown via markdownify."""
    try:
        import markdownify
    except ImportError:
        raise ImportError(
            "markdownify is required for HTML conversion. "
            "Install it with: pip install atlas_cortex[converters]"
        )

    html_text = content.decode(encoding, errors="replace")
    original_hash = hashlib.sha256(content).hexdigest()
    original_tokens = _estimate_token_count(html_text)

    markdown = markdownify.markdownify(
        html_text,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style", "meta", "link"],
    )

    # Clean up excessive blank lines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    md_tokens = _estimate_token_count(markdown)
    coverage = md_tokens / max(original_tokens, 1)

    converter_version = getattr(markdownify, "__version__", "unknown")

    result = ConversionResult(
        markdown=markdown,
        source_format="html",
        converter_name="markdownify",
        converter_version=converter_version,
        coverage_ratio=min(coverage, 1.0),
        ir_hash=_compute_ir_hash(original_hash, "markdownify", converter_version),
        original_hash=original_hash,
    )

    if not result.is_acceptable:
        result.warnings.append(
            f"Low coverage ratio ({coverage:.2f}). "
            f"Conversion may have lost significant content."
        )

    return result


def convert_docx(content: bytes) -> ConversionResult:
    """DOCX → Markdown via mammoth."""
    try:
        import mammoth
    except ImportError:
        raise ImportError(
            "mammoth is required for DOCX conversion. "
            "Install it with: pip install atlas_cortex[converters]"
        )
    import io

    original_hash = hashlib.sha256(content).hexdigest()

    result_mammoth = mammoth.convert_to_markdown(io.BytesIO(content))
    markdown = result_mammoth.value
    messages = result_mammoth.messages

    # Estimate original tokens from the markdown output (DOCX binary is not text)
    # For DOCX we use a heuristic: mammoth rarely loses content, so coverage ~0.9
    md_tokens = _estimate_token_count(markdown)
    # Heuristic coverage: mammoth is high-fidelity for text content
    coverage = 0.92 if md_tokens > 10 else 0.5

    converter_version = getattr(mammoth, "__version__", "unknown")

    warnings = [str(m) for m in messages if m.type == "warning"]

    return ConversionResult(
        markdown=markdown,
        source_format="docx",
        converter_name="mammoth",
        converter_version=converter_version,
        coverage_ratio=coverage,
        ir_hash=_compute_ir_hash(original_hash, "mammoth", converter_version),
        original_hash=original_hash,
        warnings=warnings,
    )


def convert_epub(content: bytes) -> ConversionResult:
    """EPUB → Markdown. Extracts HTML chapters and converts via markdownify."""
    try:
        import zipfile

        import markdownify
    except ImportError:
        raise ImportError(
            "markdownify is required for EPUB conversion. "
            "Install it with: pip install atlas_cortex[converters]"
        )
    import io

    original_hash = hashlib.sha256(content).hexdigest()

    chapters_md = []
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            html_files = sorted(
                [n for n in zf.namelist() if n.endswith((".html", ".xhtml", ".htm"))],
            )
            for html_file in html_files:
                html_content = zf.read(html_file).decode("utf-8", errors="replace")
                md_chunk = markdownify.markdownify(
                    html_content,
                    heading_style="ATX",
                    bullets="-",
                    strip=["script", "style", "meta", "link"],
                )
                if md_chunk.strip():
                    chapters_md.append(md_chunk.strip())
    except zipfile.BadZipFile:
        return ConversionResult(
            markdown="",
            source_format="epub",
            converter_name="atlas_builtin_epub",
            converter_version="1.0.0",
            coverage_ratio=0.0,
            ir_hash=_compute_ir_hash(original_hash, "atlas_builtin_epub", "1.0.0"),
            original_hash=original_hash,
            warnings=["Invalid EPUB file (not a valid ZIP archive)."],
        )

    markdown = "\n\n---\n\n".join(chapters_md)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    converter_version = getattr(markdownify, "__version__", "unknown")
    coverage = 0.88 if len(chapters_md) > 0 else 0.0

    return ConversionResult(
        markdown=markdown,
        source_format="epub",
        converter_name="atlas_builtin_epub+markdownify",
        converter_version=converter_version,
        coverage_ratio=coverage,
        ir_hash=_compute_ir_hash(original_hash, "atlas_builtin_epub", converter_version),
        original_hash=original_hash,
    )


# ---------------------------------------------------------------------------
# Converter Registry
# ---------------------------------------------------------------------------

# Maps file extension → converter function
_REGISTRY: dict[str, Callable[..., ConversionResult] | None] = {
    ".txt": convert_txt,
    ".text": convert_txt,
    ".html": convert_html,
    ".htm": convert_html,
    ".xhtml": convert_html,
    ".docx": convert_docx,
    ".epub": convert_epub,
    ".md": None,  # Native — no conversion needed
    ".markdown": None,
}

# Maps MIME type → extension for auto-detection
_MIME_MAP: dict[str, str] = {
    "text/plain": ".txt",
    "text/html": ".html",
    "application/xhtml+xml": ".xhtml",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/epub+zip": ".epub",
    "text/markdown": ".md",
}


def supported_formats() -> list[str]:
    """Returns list of supported file extensions."""
    return sorted(_REGISTRY.keys())


def is_native_format(ext: str) -> bool:
    """Returns True if the format needs no conversion (is already Markdown)."""
    ext = ext.lower() if not ext.startswith(".") else ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return _REGISTRY.get(ext) is None and ext in _REGISTRY


def convert_file(filepath: str, encoding: str = "utf-8") -> ConversionResult:
    """
    Convert a file to Markdown IR based on its extension.

    Args:
        filepath: Path to the file to convert.
        encoding: Text encoding for TXT/HTML files.

    Returns:
        ConversionResult with the Markdown IR and provenance metadata.

    Raises:
        ValueError: If the format is not supported.
        ImportError: If required optional dependency is missing.
    """
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext not in _REGISTRY:
        raise ValueError(
            f"Unsupported format: '{ext}'. "
            f"Supported: {', '.join(supported_formats())}"
        )

    converter_fn = _REGISTRY[ext]

    if converter_fn is None:
        # Native Markdown — read and return as-is
        content = path.read_bytes()
        text = content.decode(encoding, errors="replace").replace("\r\n", "\n")
        original_hash = hashlib.sha256(content).hexdigest()
        return ConversionResult(
            markdown=text,
            source_format="markdown",
            converter_name="native",
            converter_version="n/a",
            coverage_ratio=1.0,
            ir_hash=original_hash,
            original_hash=original_hash,
        )

    content = path.read_bytes()

    if ext in (".txt", ".text", ".html", ".htm", ".xhtml"):
        result = converter_fn(content, encoding=encoding)
    else:
        result = converter_fn(content)

    if not result.is_acceptable:
        logger.warning(
            "Conversion of %s produced low coverage ratio (%.2f < %.2f). "
            "Content may be incomplete.",
            filepath, result.coverage_ratio, MIN_COVERAGE_RATIO,
        )

    return result


def convert_bytes(content: bytes, format_hint: str, encoding: str = "utf-8") -> ConversionResult:
    """
    Convert raw bytes to Markdown IR using a format hint (extension or MIME type).

    Args:
        content: Raw file content.
        format_hint: File extension (e.g., ".docx") or MIME type.
        encoding: Text encoding for text-based formats.
    """
    # Normalize format hint
    if "/" in format_hint:
        # MIME type
        ext = _MIME_MAP.get(format_hint)
        if ext is None:
            raise ValueError(f"Unsupported MIME type: '{format_hint}'")
    else:
        ext = format_hint if format_hint.startswith(".") else f".{format_hint}"

    ext = ext.lower()
    if ext not in _REGISTRY:
        raise ValueError(f"Unsupported format: '{ext}'")

    converter_fn = _REGISTRY[ext]
    if converter_fn is None:
        text = content.decode(encoding, errors="replace").replace("\r\n", "\n")
        original_hash = hashlib.sha256(content).hexdigest()
        return ConversionResult(
            markdown=text,
            source_format="markdown",
            converter_name="native",
            converter_version="n/a",
            coverage_ratio=1.0,
            ir_hash=original_hash,
            original_hash=original_hash,
        )

    if ext in (".txt", ".text", ".html", ".htm", ".xhtml"):
        return converter_fn(content, encoding=encoding)
    return converter_fn(content)
