"""Tests for the Atlas Cortex Converter Module (Fase 10)."""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "python"))

from atlas_cortex.converters import (
    ConversionResult,
    convert_bytes,
    convert_file,
    convert_txt,
    convert_html,
    is_native_format,
    supported_formats,
    _compute_ir_hash,
    _estimate_token_count,
)


class TestConversionResult:
    def test_acceptable_high_coverage(self):
        result = ConversionResult(
            markdown="# Hello", source_format="txt",
            converter_name="test", converter_version="1.0",
            coverage_ratio=0.95, ir_hash="abc", original_hash="def",
        )
        assert result.is_acceptable

    def test_unacceptable_low_coverage(self):
        result = ConversionResult(
            markdown="", source_format="txt",
            converter_name="test", converter_version="1.0",
            coverage_ratio=0.50, ir_hash="abc", original_hash="def",
        )
        assert not result.is_acceptable

    def test_boundary_coverage(self):
        result = ConversionResult(
            markdown="ok", source_format="txt",
            converter_name="test", converter_version="1.0",
            coverage_ratio=0.75, ir_hash="abc", original_hash="def",
        )
        assert result.is_acceptable


class TestTxtConverter:
    def test_basic_txt(self):
        content = b"Hello World\nThis is a test."
        result = convert_txt(content)
        assert result.source_format == "txt"
        assert result.coverage_ratio == 1.0
        assert result.is_acceptable
        assert "Hello World" in result.markdown

    def test_crlf_normalization(self):
        content = b"Line 1\r\nLine 2\r\n"
        result = convert_txt(content)
        assert "\r\n" not in result.markdown
        assert "Line 1\nLine 2\n" == result.markdown

    def test_deterministic_hash(self):
        content = b"Determinism test"
        r1 = convert_txt(content)
        r2 = convert_txt(content)
        assert r1.ir_hash == r2.ir_hash
        assert r1.original_hash == r2.original_hash

    def test_utf8_content(self):
        content = "São Paulo é incrível — ñ, ü, ß".encode("utf-8")
        result = convert_txt(content)
        assert "São Paulo" in result.markdown


class TestHtmlConverter:
    def test_basic_html(self):
        html = b"<h1>Title</h1><p>Hello world</p>"
        try:
            result = convert_html(html)
            assert "# Title" in result.markdown or "Title" in result.markdown
            assert result.source_format == "html"
            assert result.is_acceptable
        except ImportError:
            pytest.skip("markdownify not installed")

    def test_strips_scripts(self):
        html = b"<p>Content</p><script>alert('xss')</script>"
        try:
            result = convert_html(html)
            assert "alert" not in result.markdown
            assert "Content" in result.markdown
        except ImportError:
            pytest.skip("markdownify not installed")

    def test_preserves_links(self):
        html = b'<p>Visit <a href="https://example.com">Example</a></p>'
        try:
            result = convert_html(html)
            assert "Example" in result.markdown
        except ImportError:
            pytest.skip("markdownify not installed")


class TestHelpers:
    def test_token_count_estimation(self):
        assert _estimate_token_count("hello world foo bar") == 4
        assert _estimate_token_count("") == 0
        assert _estimate_token_count("one") == 1

    def test_ir_hash_determinism(self):
        h1 = _compute_ir_hash("abc", "converter", "1.0")
        h2 = _compute_ir_hash("abc", "converter", "1.0")
        assert h1 == h2

    def test_ir_hash_changes_with_version(self):
        h1 = _compute_ir_hash("abc", "converter", "1.0")
        h2 = _compute_ir_hash("abc", "converter", "2.0")
        assert h1 != h2


class TestRegistry:
    def test_supported_formats_includes_md(self):
        formats = supported_formats()
        assert ".md" in formats
        assert ".txt" in formats
        assert ".html" in formats

    def test_is_native_format(self):
        assert is_native_format(".md")
        assert is_native_format(".markdown")
        assert not is_native_format(".html")
        assert not is_native_format(".docx")

    def test_unsupported_format_raises(self):
        fd, path = tempfile.mkstemp(suffix=".xyz")
        try:
            os.write(fd, b"test")
            os.close(fd)
            with pytest.raises(ValueError, match="Unsupported format"):
                convert_file(path)
        finally:
            os.unlink(path)


class TestConvertBytes:
    def test_txt_via_bytes(self):
        result = convert_bytes(b"Hello", ".txt")
        assert result.source_format == "txt"
        assert result.is_acceptable

    def test_mime_type_lookup(self):
        result = convert_bytes(b"Hello", "text/plain")
        assert result.source_format == "txt"

    def test_unsupported_mime_raises(self):
        with pytest.raises(ValueError, match="Unsupported MIME"):
            convert_bytes(b"data", "application/octet-stream")


class TestConvertFile:
    def test_convert_md_file(self):
        fd, path = tempfile.mkstemp(suffix=".md")
        try:
            os.write(fd, b"# Test\nHello world")
            os.close(fd)
            result = convert_file(path)
            assert result.source_format == "markdown"
            assert result.converter_name == "native"
            assert result.coverage_ratio == 1.0
        finally:
            os.unlink(path)

    def test_convert_txt_file(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            os.write(fd, b"Plain text content here")
            os.close(fd)
            result = convert_file(path)
            assert result.source_format == "txt"
            assert "Plain text content here" in result.markdown
        finally:
            os.unlink(path)
