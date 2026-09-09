"""Écrit — main application entry point."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

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
from ecrit.ui.overlays.command_palette import CommandPalette
from ecrit.ui.overlays.sprint_timer import SprintTimerWidget
from ecrit.ui.overlays.reading_mode import ReadingMode
from ecrit.ui.overlays.scratchpad import Scratchpad
from ecrit.ui.overlays.character_sheet import CharacterSheet
from ecrit.ui.overlays.compare_drafts import CompareDrafts
from ecrit.ui.overlays.snapshots import (
    SnapshotsDialog, list_snapshots, get_snapshot_content, create_snapshot,
)
from ecrit.ui.overlays.reports import ReportsDialog
from ecrit.ui.overlays.logline_builder import LoglineBuilderDialog
from ecrit.ui.overlays.series_panel import SeriesPanel
from ecrit.ui.overlays.sync_settings import SyncSettingsDialog
from ecrit.ui.overlays.cloud_export import CloudExportDialog
from ecrit.ui.overlays.share_review import ShareReviewDialog
from ecrit.screenplay.series_projects import SeriesProject
from ecrit.export.share_review import generate_review_html, generate_share_link, list_shares


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
        self.title_bar.cmd_chip.clicked.connect(self._show_command_palette)
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
        self.editor.sprint_clicked.connect(self._show_sprint_timer)
        self.editor.theme_toggle_requested.connect(self._toggle_theme)
        self.editor.character_activated.connect(self._open_character_sheet)
        self.editor.export_pdf_requested.connect(lambda: self._export_script("pdf"))
        self.editor.export_odt_requested.connect(lambda: self._export_script("odt"))
        self.editor.export_fountain_requested.connect(lambda: self._export_script("fountain"))
        self.stack.addWidget(self.editor)

        self._editor_title_bar = TitleBar(show_phases=True)
        self._editor_title_bar.settings_clicked.connect(self._open_settings)
        self._editor_title_bar.home_clicked.connect(self._go_dashboard)
        self._editor_title_bar.phase_changed.connect(self._on_phase_changed)
        self._editor_title_bar.cmd_chip.clicked.connect(self._show_command_palette)

        self._stats_dialog = StatsDialog(self)
        self._shortcuts_dialog = ShortcutsDialog(self)
        self._settings_dialog = SettingsDialog(self)
        self._settings_dialog.theme_changed.connect(self._apply_theme)

        self._command_palette = CommandPalette(self)
        self._command_palette.command_selected.connect(self._on_command)

        self._sprint_timer = SprintTimerWidget(self)
        self._sprint_timer.sprint_ended.connect(self._on_sprint_ended)

        self._character_sheet = CharacterSheet(self)
        self._character_sheet.character_saved.connect(self._on_character_saved)

        self._compare_drafts = CompareDrafts(self)

        self._snapshots_dialog = SnapshotsDialog(self)
        self._snapshots_dialog.snapshot_restored.connect(self._on_snapshot_restored)

        self._reports_dialog = ReportsDialog(self)
        self._logline_dialog = LoglineBuilderDialog(self)
        self._logline_dialog.logline_ready.connect(self._on_logline_ready)

        self._series_panel = SeriesPanel(self)
        self._series_panel.episode_selected.connect(self._on_episode_selected)

        self._sync_dialog = SyncSettingsDialog(self)
        self._sync_dialog.sync_requested.connect(self._on_sync_requested)

        self._cloud_export_dialog = CloudExportDialog(self)
        self._cloud_export_dialog.export_requested.connect(self._on_cloud_export)

        self._share_dialog = ShareReviewDialog(self)
        self._share_dialog.share_created.connect(self._on_share_created)

        self._cmd_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self._cmd_palette_shortcut.activated.connect(self._show_command_palette)

        self._sprint_status_timer = QTimer(self)
        self._sprint_status_timer.setInterval(1000)
        self._sprint_status_timer.timeout.connect(self._update_sprint_label)
        self._sprint_status_timer.start()

        self._apply_theme()
        self._go_dashboard()

    def _apply_theme(self):
        t = theme.current()
        self.setStyleSheet(generate(t))

    def _go_dashboard(self):
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
            try:
                self.editor.manuscript.editor.content_changed.disconnect(self._on_content_changed)
            except RuntimeError:
                pass
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

    def _on_command(self, name: str):
        phases = {"Plan", "Outline", "Manuscript", "Proofread", "Deliver"}
        if name in phases:
            self._switch_phase(name)
            return

        handlers = {
            "Dashboard": self._go_dashboard,
            "New Project": self._show_new_project,
            "Import Script": self._import_script,
            "Open Project": self._go_dashboard,
            "Save": self._save_script,
            "Find & Replace": self.editor._toggle_find,
            "Statistics": self._show_stats,
            "Keyboard Shortcuts": self._show_shortcuts,
            "Settings": self._open_settings,
            "Toggle Theme": self._toggle_theme,
            "Reading Mode": self._enter_reading_mode,
            "Sprint Timer": self._show_sprint_timer,
            "Scratchpad": self._toggle_scratchpad,
            "Snapshot": self._create_snapshot,
            "Compare Drafts": self._show_compare_drafts,
            "Export PDF": lambda: self._export_script("pdf"),
            "Export ODT": lambda: self._export_script("odt"),
            "Export Fountain": lambda: self._export_script("fountain"),
            "Production Reports": self._show_reports,
            "Logline Builder": self._show_logline_builder,
            "Series Manager": self._show_series_manager,
            "Remote Sync": self._show_sync_settings,
            "Cloud Export": self._show_cloud_export,
            "Share for Review": self._show_share_review,
        }
        handler = handlers.get(name)
        if handler:
            handler()

    def _show_command_palette(self):
        geo = self.geometry()
        x = geo.x() + (geo.width() - self._command_palette.width()) // 2
        y = geo.y() + 90
        self._command_palette.move(x, y)
        self._command_palette.show()
        self._command_palette.raise_()
        self._command_palette.setFocus()

    def _switch_phase(self, phase: str):
        if self.stack.currentWidget() is not self.editor:
            return
        if self._editor_title_bar.phase_tabs:
            self._editor_title_bar.phase_tabs.set_active(phase)

    def _save_script(self):
        if self.stack.currentWidget() is not self.editor:
            return
        self._on_content_changed()

    def _enter_reading_mode(self):
        if self.stack.currentWidget() is not self.editor:
            return
        self.editor.enter_reading_mode()

    def _show_sprint_timer(self):
        geo = self.geometry()
        x = geo.x() + geo.width() - self._sprint_timer.width() - 24
        y = geo.y() + geo.height() - self._sprint_timer.height() - 48
        self._sprint_timer.move(x, y)
        self._sprint_timer.show()

    def _on_sprint_ended(self, minutes: int):
        self.editor.status_bar.sprint_label.setText(f"Sprint complete — {minutes}m")

    def _update_sprint_label(self):
        text = self._sprint_timer.get_status_text()
        if text:
            self.editor.status_bar.sprint_label.setText(text)

    def _toggle_scratchpad(self):
        if self.stack.currentWidget() is not self.editor:
            return
        self.editor.toggle_scratchpad()

    def _open_character_sheet(self, data: dict):
        self._character_sheet.set_character(data)
        self._character_sheet.exec()

    def _on_character_saved(self, data: dict):
        rail = self.editor.manuscript.char_rail
        original_name = self._character_sheet._data.get("name", "")
        updated = []
        found = False
        for ch in rail._characters:
            if ch.get("name") == original_name:
                updated.append(data)
                found = True
            else:
                updated.append(ch)
        if not found:
            updated.append(data)
        rail.update_characters(updated)

    def _create_snapshot(self):
        if not STATE.current_project_path:
            return
        create_snapshot(STATE.current_project_path)
        self._snapshots_dialog.set_project(STATE.current_project_path)
        self._snapshots_dialog.exec()

    def _show_compare_drafts(self):
        if self.stack.currentWidget() is not self.editor or not STATE.current_project_path:
            return
        snapshots = list_snapshots(STATE.current_project_path)
        self._compare_drafts.set_snapshots(snapshots)
        current_text = self.editor.manuscript.editor.toPlainText()
        from_text = ""
        if snapshots:
            idx = 1 if len(snapshots) > 1 else 0
            from_text = get_snapshot_content(STATE.current_project_path, snapshots[idx]["hash"])
        self._compare_drafts.set_texts(from_text, current_text)
        self._compare_drafts.exec()

    def _on_snapshot_restored(self, content: str):
        if not content:
            return
        self.editor.manuscript.editor.setPlainText(content)
        self.editor.proofread.script_view.setPlainText(content)
        STATE.script_content = content
        STATE.save_script()
        self._editor_title_bar.save_dot.set_saved(True)

    def _show_reports(self):
        if self.stack.currentWidget() is not self.editor:
            return
        script = self.editor.manuscript.editor.toPlainText()
        self._reports_dialog.set_script(script)
        self._reports_dialog.exec()

    def _show_logline_builder(self):
        self._logline_dialog.exec()

    def _on_logline_ready(self, logline: str):
        if self.stack.currentWidget() is self.editor:
            self.editor.plan.editor.append(f"\nLogline: {logline}")

    def _show_series_manager(self):
        if not hasattr(self, "_series_project") or self._series_project is None:
            self._series_project = SeriesProject(title="Untitled Series")
            self._series_project.add_season("Season 1")
        self._series_panel.set_project(self._series_project)
        self._series_panel.exec()

    def _on_episode_selected(self, season: int, episode: int):
        pass

    def _show_sync_settings(self):
        if STATE.current_project_path:
            from ecrit.sync.remote_sync import load_remote_config
            config = load_remote_config(STATE.current_project_path)
            if config:
                self._sync_dialog.set_config({
                    "provider": config.provider.value if hasattr(config.provider, "value") else config.provider,
                    "remote_url": config.remote_url,
                    "username": config.username,
                    "branch": config.branch,
                    "auto_sync": config.auto_sync,
                })
        self._sync_dialog.exec()

    def _on_sync_requested(self, action: str):
        if not STATE.current_project_path:
            return
        config_dict = self._sync_dialog.get_config()
        from ecrit.sync.remote_sync import (
            RemoteConfig, RemoteProvider, push_to_remote, pull_from_remote,
            save_remote_config,
        )
        try:
            provider = RemoteProvider(config_dict["provider"])
        except (ValueError, KeyError):
            provider = RemoteProvider.GITHUB
        config = RemoteConfig(
            provider=provider,
            remote_url=config_dict.get("remote_url", ""),
            username=config_dict.get("username", ""),
            token=config_dict.get("token", ""),
            branch=config_dict.get("branch", "main"),
            auto_sync=config_dict.get("auto_sync", False),
        )
        save_remote_config(STATE.current_project_path, config)
        try:
            if action == "push":
                result = push_to_remote(STATE.current_project_path, config)
            else:
                result = pull_from_remote(STATE.current_project_path, config)
            self._sync_dialog.set_status(f"{result.status.value}: {result.message}")
        except Exception as exc:
            self._sync_dialog.set_status(f"error: {exc}")

    def _show_cloud_export(self):
        self._cloud_export_dialog.exec()

    def _on_cloud_export(self, provider: str, fmt: str):
        if self.stack.currentWidget() is not self.editor:
            return
        content = self.editor.manuscript.editor.toPlainText()
        title = self._editor_title_bar.context_label.text() or "Untitled"
        from ecrit.sync.cloud_export import export_script, CloudProvider
        try:
            cp = CloudProvider(provider)
        except (ValueError, KeyError):
            return
        if STATE.current_project_path:
            try:
                result = export_script(STATE.current_project_path, cp, content, f"{title}.{fmt}", fmt)
                self._cloud_export_dialog.add_history_entry(
                    f"{'✅' if result.success else '❌'} {result.message}"
                )
            except Exception as exc:
                self._cloud_export_dialog.add_history_entry(f"❌ Export failed: {exc}")

    def _show_share_review(self):
        if STATE.current_project_path:
            shares = list_shares(STATE.current_project_path)
            self._share_dialog.set_shares(shares)
        self._share_dialog.exec()

    def _on_share_created(self, watermark: str):
        if self.stack.currentWidget() is not self.editor or not STATE.current_project_path:
            return
        content = self.editor.manuscript.editor.toPlainText()
        title = self._editor_title_bar.context_label.text() or "Untitled"
        html = generate_review_html(content, title, author="", watermark_text=watermark)
        path = generate_share_link(html, STATE.current_project_path)
        import datetime
        self._share_dialog.add_share({
            "title": title,
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "path": path,
        })

    def _export_script(self, kind: str):
        if self.stack.currentWidget() is not self.editor:
            return
        content = self.editor.manuscript.editor.toPlainText()
        title = self._editor_title_bar.context_label.text() or "Untitled"
        if kind == "pdf":
            from ecrit.export.pdf_export import export_pdf
            export_pdf(content, title=title, parent=self)
        elif kind == "odt":
            from ecrit.export.odt_export import export_odt
            export_odt(content, title=title, parent=self)
        elif kind == "fountain":
            from ecrit.export.fountain_export import export_fountain
            export_fountain(content, title=title, parent=self)

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
