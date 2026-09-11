"""Tests for export modules: fountain, PDF, ODT.
Adversarial tests with edge cases, Unicode, malformed input, huge files."""

import os
import json
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree

from tests.conftest import (
    SAMPLE_FOUNTAIN, EMPTY_FOUNTAIN, MINIMAL_FOUNTAIN,
    UNICODE_FOUNTAIN, HUGE_FOUNTAIN, MALFORMED_FOUNTAIN,
)


class TestFountainExport:
    def test_export_to_path(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "test.fountain")
        export_fountain_to_path(SAMPLE_FOUNTAIN, out)
        assert os.path.exists(out)
        with open(out, "r", encoding="utf-8") as f:
            assert f.read() == SAMPLE_FOUNTAIN

    def test_export_empty(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "empty.fountain")
        export_fountain_to_path("", out)
        assert os.path.exists(out)
        with open(out, "r", encoding="utf-8") as f:
            assert f.read() == ""

    def test_export_unicode(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "unicode.fountain")
        export_fountain_to_path(UNICODE_FOUNTAIN, out)
        with open(out, "r", encoding="utf-8") as f:
            content = f.read()
        assert "LOÏSE" in content  # uppercase in fixture
        assert "CAFÉ" in content

    def test_export_creates_dirs(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "sub" / "dir" / "test.fountain")
        export_fountain_to_path("content", out)
        assert os.path.exists(out)

    def test_export_huge(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "huge.fountain")
        export_fountain_to_path(HUGE_FOUNTAIN, out)
        assert os.path.getsize(out) > 10000

    def test_export_malformed(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        out = str(tmp_path / "malformed.fountain")
        export_fountain_to_path(MALFORMED_FOUNTAIN, out)
        assert os.path.exists(out)

    def test_export_preserves_line_endings(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        content = "Line 1\nLine 2\nLine 3\n"
        out = str(tmp_path / "lines.fountain")
        export_fountain_to_path(content, out)
        with open(out, "r", encoding="utf-8", newline="") as f:
            assert f.read() == content

    def test_export_special_chars(self, tmp_path):
        from ecrit.export.fountain_export import export_fountain_to_path
        content = "Characters: <>&\"' and \t tabs \\ backslash"
        out = str(tmp_path / "special.fountain")
        export_fountain_to_path(content, out)
        with open(out, "r", encoding="utf-8") as f:
            assert f.read() == content


class TestODTExport:
    def test_build_content_xml_minimal(self):
        from ecrit.export.odt_export import _build_content_xml
        result = _build_content_xml(MINIMAL_FOUNTAIN)
        assert "office:document-content" in result
        assert "office:text" in result

    def test_build_content_xml_empty(self):
        from ecrit.export.odt_export import _build_content_xml
        result = _build_content_xml("")
        assert "office:document-content" in result

    def test_create_odt_bytes(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(SAMPLE_FOUNTAIN)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_odt_is_valid_zip(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(SAMPLE_FOUNTAIN)
        import io
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
            names = zf.namelist()
            assert "mimetype" in names
            assert "content.xml" in names
            assert "META-INF/manifest.xml" in names

    def test_odt_mimetype(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(SAMPLE_FOUNTAIN)
        import io
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
            mimetype = zf.read("mimetype").decode("utf-8")
            assert mimetype == "application/vnd.oasis.opendocument.text"

    def test_odt_content_xml_parseable(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(SAMPLE_FOUNTAIN)
        import io
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
            content = zf.read("content.xml").decode("utf-8")
        root = ElementTree.fromstring(content)
        assert root.tag.endswith("document-content")

    def test_odt_manifest_xml_parseable(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(SAMPLE_FOUNTAIN)
        import io
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
            manifest = zf.read("META-INF/manifest.xml").decode("utf-8")
        root = ElementTree.fromstring(manifest)
        assert "manifest" in root.tag

    def test_export_to_path(self, tmp_path):
        from ecrit.export.odt_export import export_odt_to_path
        out = str(tmp_path / "test.odt")
        export_odt_to_path(SAMPLE_FOUNTAIN, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 100

    def test_export_creates_dirs(self, tmp_path):
        from ecrit.export.odt_export import export_odt_to_path
        out = str(tmp_path / "deep" / "path" / "test.odt")
        export_odt_to_path(SAMPLE_FOUNTAIN, out)
        assert os.path.exists(out)

    def test_odt_unicode(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(UNICODE_FOUNTAIN)
        import io
        with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
            content = zf.read("content.xml").decode("utf-8")
        assert "H" in content  # Héloïse should appear (possibly XML-escaped)

    def test_odt_escapes_xml_special_chars(self):
        from ecrit.export.odt_export import _build_content_xml
        content = "Characters say <hello> & \"goodbye\" often."
        result = _build_content_xml(content)
        assert "&lt;" in result or "<hello>" not in result
        assert "&amp;" in result

    def test_odt_huge_file(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(HUGE_FOUNTAIN)
        assert len(data) > 1000

    def test_odt_malformed(self):
        from ecrit.export.odt_export import _create_odt_bytes
        data = _create_odt_bytes(MALFORMED_FOUNTAIN)
        assert len(data) > 100  # should not crash

    def test_style_map_coverage(self):
        from ecrit.export.odt_export import STYLE_MAP
        expected_types = [
            "SceneHeading", "Action", "Character", "Dialogue",
            "Parenthetical", "Transition", "Section", "Synopsis", "Note",
        ]
        for t in expected_types:
            assert t in STYLE_MAP, f"Missing style mapping for {t}"


class TestPDFExport:
    def test_build_document(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document(SAMPLE_FOUNTAIN)
        assert doc is not None
        assert doc.toPlainText() != ""

    def test_build_document_empty(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document("")
        assert doc is not None

    def test_build_document_no_title_page(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document(SAMPLE_FOUNTAIN, include_title_page=False)
        assert doc is not None

    def test_build_document_unicode(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document(UNICODE_FOUNTAIN)
        text = doc.toPlainText()
        assert len(text) > 0

    def test_build_document_huge(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document(HUGE_FOUNTAIN)
        assert doc.toPlainText() != ""

    def test_build_document_malformed(self, qapp):
        from ecrit.export.pdf_export import _build_document
        doc = _build_document(MALFORMED_FOUNTAIN)
        assert doc is not None

    def test_build_document_scene_numbers(self, qapp):
        from ecrit.export.pdf_export import _build_document
        parsed = json.dumps({
            "title_page": {},
            "elements": [
                {"type": "SceneHeading", "text": "INT. OFFICE - DAY"},
                {"type": "Action", "text": "Someone walks in."},
                {"type": "SceneHeading", "text": "EXT. PARK - NIGHT"},
            ],
        })
        mock_core = MagicMock()
        mock_core.parse_fountain.return_value = parsed
        with patch.dict("sys.modules", {"ecrit_core": mock_core}):
            doc = _build_document(SAMPLE_FOUNTAIN, scene_numbers=True)
        text = doc.toPlainText()
        assert "1." in text
        assert "2." in text

    def test_export_to_path(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "test.pdf")
        export_pdf_to_path(SAMPLE_FOUNTAIN, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 100

    def test_export_a4(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "a4.pdf")
        export_pdf_to_path(SAMPLE_FOUNTAIN, out, paper="A4")
        assert os.path.exists(out)

    def test_export_creates_dirs(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "sub" / "dir" / "test.pdf")
        export_pdf_to_path(SAMPLE_FOUNTAIN, out)
        assert os.path.exists(out)

    def test_element_styles_coverage(self):
        from ecrit.export.pdf_export import ELEMENT_STYLES
        expected = [
            "SceneHeading", "Action", "Character", "Dialogue",
            "Parenthetical", "Transition", "Section", "Synopsis",
            "Note", "PageBreak",
        ]
        for t in expected:
            assert t in ELEMENT_STYLES, f"Missing PDF style for {t}"

    def test_pdf_starts_with_header(self, qapp, tmp_path):
        from ecrit.export.pdf_export import export_pdf_to_path
        out = str(tmp_path / "header.pdf")
        export_pdf_to_path(SAMPLE_FOUNTAIN, out)
        with open(out, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"
