"""PDF export — paginate Fountain script to PDF using Qt's print engine."""

import json
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QMarginsF, QSizeF, Qt
from PySide6.QtGui import (
    QFont, QPageLayout, QPageSize, QTextDocument,
    QTextCursor, QTextCharFormat, QTextBlockFormat
)
from PySide6.QtPrintSupport import QPrinter


ELEMENT_STYLES = {
    "SceneHeading": {"bold": True, "upper": True, "align": Qt.AlignmentFlag.AlignLeft, "margin_top": 24},
    "Action": {"align": Qt.AlignmentFlag.AlignLeft, "margin_top": 12},
    "Character": {"upper": True, "align": Qt.AlignmentFlag.AlignCenter, "margin_top": 12, "left_indent": 144},
    "Dialogue": {"align": Qt.AlignmentFlag.AlignLeft, "left_indent": 72, "right_indent": 144},
    "Parenthetical": {"align": Qt.AlignmentFlag.AlignLeft, "left_indent": 108},
    "Transition": {"upper": True, "align": Qt.AlignmentFlag.AlignRight, "margin_top": 12},
    "Section": {"bold": True, "margin_top": 18},
    "Synopsis": {"italic": True},
    "Note": {"italic": True},
    "PageBreak": {"page_break": True},
}


def _build_document(script_content: str, font_size: int = 12, include_title_page: bool = True, scene_numbers: bool = False) -> QTextDocument:
    doc = QTextDocument()
    font = QFont("Courier Prime", font_size)
    doc.setDefaultFont(font)

    cursor = QTextCursor(doc)

    try:
        import ecrit_core
        parsed = json.loads(ecrit_core.parse_fountain(script_content))
    except Exception:
        cursor.insertText(script_content)
        return doc

    if include_title_page:
        title_page = parsed.get("title_page", {})
        if title_page:
            title_fmt = QTextCharFormat()
            title_fmt.setFont(QFont("Courier Prime", 18))
            title_fmt.setFontWeight(QFont.Weight.Bold)

            block_fmt = QTextBlockFormat()
            block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            block_fmt.setTopMargin(120)

            cursor.setBlockFormat(block_fmt)
            cursor.insertText(title_page.get("title", ""), title_fmt)

            if title_page.get("credit"):
                cursor.insertBlock()
                normal_fmt = QTextCharFormat()
                normal_fmt.setFont(QFont("Courier Prime", 12))
                block_fmt.setTopMargin(24)
                cursor.setBlockFormat(block_fmt)
                cursor.insertText(title_page["credit"], normal_fmt)

            if title_page.get("author"):
                cursor.insertBlock()
                cursor.setBlockFormat(block_fmt)
                cursor.insertText(title_page["author"], normal_fmt)

            # Force page break after title
            cursor.insertBlock()
            break_fmt = QTextBlockFormat()
            break_fmt.setPageBreakPolicy(QTextBlockFormat.PageBreakFlag.PageBreak_AlwaysAfter)
            cursor.setBlockFormat(break_fmt)

    elements = parsed.get("elements", [])
    scene_num = 0
    for elem in elements:
        kind = elem.get("type", "Action")
        text = elem.get("text", "")
        style = ELEMENT_STYLES.get(kind, {})

        if style.get("page_break"):
            block_fmt = QTextBlockFormat()
            block_fmt.setPageBreakPolicy(QTextBlockFormat.PageBreakFlag.PageBreak_AlwaysAfter)
            cursor.insertBlock()
            cursor.setBlockFormat(block_fmt)
            continue

        cursor.insertBlock()

        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(style.get("align", Qt.AlignmentFlag.AlignLeft))
        block_fmt.setTopMargin(style.get("margin_top", 0))
        if "left_indent" in style:
            block_fmt.setLeftMargin(style["left_indent"])
        if "right_indent" in style:
            block_fmt.setRightMargin(style["right_indent"])
        cursor.setBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        char_fmt.setFont(QFont("Courier Prime", font_size))
        if style.get("bold"):
            char_fmt.setFontWeight(QFont.Weight.Bold)
        if style.get("italic"):
            char_fmt.setFontItalic(True)

        display_text = text.upper() if style.get("upper") else text
        if scene_numbers and kind == "SceneHeading":
            scene_num += 1
            display_text = f"{scene_num}. {display_text}"
        cursor.insertText(display_text, char_fmt)

    return doc


def export_pdf(
    script_content: str,
    title: str = "Untitled",
    paper: str = "USLetter",
    include_title_page: bool = True,
    scene_numbers: bool = False,
    parent=None,
) -> str:
    default_name = f"{title}.pdf"
    path, _ = QFileDialog.getSaveFileName(
        parent, "Export PDF",
        default_name,
        "PDF files (*.pdf);;All files (*)"
    )
    if not path:
        return ""

    if not path.endswith(".pdf"):
        path += ".pdf"

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)

    if paper == "A4":
        page_size = QPageSize(QPageSize.PageSizeId.A4)
    else:
        page_size = QPageSize(QPageSize.PageSizeId.Letter)

    margins = QMarginsF(72, 72, 72, 72)
    layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, margins)
    printer.setPageLayout(layout)

    doc = _build_document(script_content, include_title_page=include_title_page, scene_numbers=scene_numbers)
    doc.setPageSize(QSizeF(printer.pageRect(QPrinter.Unit.Point).size()))
    doc.print_(printer)

    return path


def export_pdf_to_path(
    script_content: str,
    path: str,
    paper: str = "USLetter",
    include_title_page: bool = True,
):
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)

    if paper == "A4":
        page_size = QPageSize(QPageSize.PageSizeId.A4)
    else:
        page_size = QPageSize(QPageSize.PageSizeId.Letter)

    margins = QMarginsF(72, 72, 72, 72)
    layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, margins)
    printer.setPageLayout(layout)

    doc = _build_document(script_content, include_title_page=include_title_page)
    doc.setPageSize(QSizeF(printer.pageRect(QPrinter.Unit.Point).size()))
    doc.print_(printer)
