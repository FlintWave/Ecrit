"""Écrit — main application entry point."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from ecrit.ui.styles import theme
from ecrit.ui.styles.stylesheet import generate
from ecrit.ui.components.title_bar import TitleBar
from ecrit.ui.screens.dashboard import Dashboard
from ecrit.ui.screens.editor import EditorScreen
from ecrit.ui.screens.new_project import NewProjectWizard
from ecrit.stores.app_state import STATE
from ecrit.ui.overlays.statistics import StatsDialog
from ecrit.ui.overlays.shortcuts import ShortcutsDialog
from ecrit.ui.overlays.settings import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Écrit")
        self.setMinimumSize(1100, 700)
        self.resize(1440, 900)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar(show_phases=False)
        self.title_bar.settings_clicked.connect(self._open_settings)
        self.title_bar.home_clicked.connect(self._go_dashboard)
        root.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.dashboard = Dashboard()
        self.dashboard.open_project.connect(self._open_project)
        self.dashboard.new_project.connect(self._show_new_project)
        self.dashboard.import_script.connect(self._import_script)
        self.stack.addWidget(self.dashboard)

        self.new_project_wizard = NewProjectWizard()
        self.new_project_wizard.project_created.connect(self._on_project_created)
        self.new_project_wizard.cancelled.connect(self._go_dashboard)
        self.stack.addWidget(self.new_project_wizard)

        self.editor = EditorScreen()
        self.editor.go_home.connect(self._go_dashboard)
        self.editor.status_bar.stats_clicked.connect(self._show_stats)
        self.editor.status_bar.shortcuts_clicked.connect(self._show_shortcuts)
        self.stack.addWidget(self.editor)

        self._editor_title_bar = TitleBar(show_phases=True)
        self._editor_title_bar.settings_clicked.connect(self._open_settings)
        self._editor_title_bar.home_clicked.connect(self._go_dashboard)
        self._editor_title_bar.phase_changed.connect(self._on_phase_changed)

        self._stats_dialog = StatsDialog(self)
        self._shortcuts_dialog = ShortcutsDialog(self)
        self._settings_dialog = SettingsDialog(self)
        self._settings_dialog.theme_changed.connect(self._apply_theme)

        self._apply_theme()
        self._go_dashboard()

    def _apply_theme(self):
        t = theme.current()
        self.setStyleSheet(generate(t))

    def _go_dashboard(self):
        root = self.centralWidget().layout()
        self._swap_title_bar(show_phases=False)
        self.title_bar.set_context("")
        self.stack.setCurrentWidget(self.dashboard)
        self.dashboard.refresh()

    def _show_new_project(self):
        self._swap_title_bar(show_phases=False)
        self.title_bar.set_context("New Project")
        self.stack.setCurrentWidget(self.new_project_wizard)
        self.new_project_wizard.reset()

    def _open_project(self, path: str):
        if not path:
            return
        data = STATE.open_project(path)
        if data:
            self._swap_title_bar(show_phases=True)
            title = data.get("meta", {}).get("title", "Untitled")
            self._editor_title_bar.set_context(title)
            self._editor_title_bar.set_wordmark_accent()
            dialect = data.get("meta", {}).get("format_id", "fountain/core")
            self.editor.status_bar.update_info(dialect=dialect)
            self.editor.load_project(data)
            self.editor.manuscript.editor.content_changed.connect(self._on_content_changed)
            self.stack.setCurrentWidget(self.editor)

    def _on_content_changed(self):
        STATE.script_content = self.editor.manuscript.editor.toPlainText()
        STATE.save_script()
        self._editor_title_bar.save_dot.set_saved(True)

    def _on_project_created(self, path: str):
        self._open_project(path)

    def _on_phase_changed(self, phase: str):
        STATE.set_phase(phase)
        self.editor.switch_phase(phase)

    def _open_settings(self):
        self._settings_dialog.load_state()
        self._settings_dialog.exec()

    def _show_stats(self):
        stats = STATE.get_stats()
        self._stats_dialog.set_stats(stats)
        self._stats_dialog.exec()

    def _show_shortcuts(self):
        self._shortcuts_dialog.exec()

    def _import_script(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Fountain Script", "",
            "Fountain files (*.fountain *.ftn);;All files (*)"
        )
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                import os
                title = os.path.splitext(os.path.basename(path))[0]
                meta = STATE.create_project(title=title, author="", format_id="fountain/core", paper="USLetter")
                if meta:
                    STATE.script_content = content
                    STATE.save_script()
                    self._open_project(meta.get("path", ""))
            except Exception:
                pass

    def _swap_title_bar(self, show_phases: bool):
        root = self.centralWidget().layout()
        old_bar = root.itemAt(0).widget()
        if show_phases and old_bar is not self._editor_title_bar:
            root.replaceWidget(old_bar, self._editor_title_bar)
            old_bar.hide()
            self._editor_title_bar.show()
        elif not show_phases and old_bar is self._editor_title_bar:
            root.replaceWidget(old_bar, self.title_bar)
            old_bar.hide()
            self.title_bar.show()

    def _toggle_theme(self):
        theme.toggle()
        self._apply_theme()

    def mousePressEvent(self, event):
        if event.position().y() < 44:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            self._drag_pos = None

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos') and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.position().y() < 44:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Écrit")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
