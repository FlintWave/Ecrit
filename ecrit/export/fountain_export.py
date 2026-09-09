"""Export script as .fountain file."""

import os
from PySide6.QtWidgets import QFileDialog


def export_fountain(script_content: str, title: str = "Untitled", parent=None) -> str:
    default_name = f"{title}.fountain"
    path, _ = QFileDialog.getSaveFileName(
        parent, "Export Fountain",
        default_name,
        "Fountain files (*.fountain);;All files (*)"
    )
    if path:
        if not path.endswith(".fountain"):
            path += ".fountain"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        return path
    return ""


def export_fountain_to_path(script_content: str, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(script_content)
