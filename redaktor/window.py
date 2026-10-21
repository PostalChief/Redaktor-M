import os

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QSplitter, QFileDialog,
    QMessageBox, QFontDialog, QInputDialog, QWidget, QVBoxLayout
)
from PySide6.QtGui import QKeySequence, QTextCursor, QAction
from PySide6.QtCore import Qt, QDir, QByteArray, QTimer
from .version import __version__
from .commands import Command, CommandRegistry
from .palette import CommandPalette
from .editor import CodeEditor
from .highlighter import PythonHighlighter
from .pygments_highlighter import PygmentsHighlighter
from .spellchecker import SpellChecker
from .filetree import FileTree
from .findpanel import FindPanel
from .filefinder import FileFinder
from .session import save_session, load_session
from .i18n import tr, set_language, get_language, LANGUAGES
from .config import load_config, save_config
from .recent import load_recent, add_recent, clear_recent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Redaktor-M")
        self.resize(1200, 750)

        self.commands = CommandRegistry()

        # Загружаем конфиг
        self.cfg = load_config()
        set_language(self.cfg.get("language", "ru"))
        self.autosave_enabled = self.cfg.get("autosave", False)
        self.utf8_bom_enabled = self.cfg.get("utf8_bom", False)

        # Таймер автосохранения
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(1500)
        self._autosave_timer.timeout.connect(self._do_autosave)

        # Недавние файлы
        self._recent = load_recent()

        # ---------- Вкладки ----------
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_title)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #2d2d30; color: #d4d4d4;
                padding: 6px 12px;
            }
            QTabBar::tab:selected { background: #1e1e1e; }
        """)

        # ---------- Сайдбар ----------
        self.file_tree = FileTree()
        self.file_tree.on_file_double_clicked = self.open_path
        self.file_tree.on_folder_changed = self._on_project_folder_changed

        # ---------- Сплиттер ----------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.file_tree)
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 940])
        self.splitter.setStyleSheet("QSplitter::handle { background: #3c3c3c; }")

        # ---------- Панель поиска ----------
        self.find_panel = FindPanel(self.current_editor)

        # ---------- Центральный виджет ----------
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.splitter, 1)
        central_layout.addWidget(self.find_panel)
        self.setCentralWidget(central)

        self.status = self.statusBar()

        # ---------- Палитра и finder ДО регистрации команд ----------
        self.palette = CommandPalette(self.commands, self)

        self.file_finder = FileFinder(self)
        self.file_finder.set_on_open(self.open_path)

        # ---------- Команды и меню ----------
        self._register_commands()
        self._build_menu_from_commands()

        # ---------- Обновляем UI-тексты под текущий язык ----------
        self._refresh_ui_texts()

        # ---------- Восстановление сессии ----------
        session = load_session()
        self._restore_session(session)

    # ============================================================
    #  РЕГИСТРАЦИЯ КОМАНД
    # ============================================================
    def _register_commands(self):
        reg = self.commands.register

        # --- File ---
        reg(Command("file.new", "file.new", "File", self.new_file, "Ctrl+N",
                    keywords=["new", "file", "create"]))
        reg(Command("file.open", "file.open", "File", self.open_file, "Ctrl+O",
                    keywords=["open", "file"]))
        reg(Command("file.open_folder", "file.open_folder", "File",
                    self.file_tree.choose_folder, "Ctrl+K",
                    keywords=["open", "folder", "project", "directory"]))
        reg(Command("file.save", "file.save", "File", self.save_file, "Ctrl+S",
                    keywords=["save", "file", "write"]))
        reg(Command("file.save_as", "file.save_as", "File",
                    self.save_file_as, "Ctrl+Shift+S",
                    keywords=["save", "as", "file"]))
        reg(Command("file.close_tab", "file.close_tab", "File",
                    lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W",
                    keywords=["close", "tab"]))
        reg(Command("file.exit", "file.exit", "File", self.close, "Ctrl+Q",
                    keywords=["exit", "quit", "close"]))
        reg(Command("file.autosave", "file.autosave", "File",
                    self.toggle_autosave, None,
                    keywords=["autosave", "auto", "save"]))

        # --- Edit ---
        reg(Command("edit.undo", "edit.undo", "Edit",
                    lambda: self._ed("undo"), "Ctrl+Z", keywords=["undo"]))
        reg(Command("edit.redo", "edit.redo", "Edit",
                    lambda: self._ed("redo"), "Ctrl+Y", keywords=["redo"]))
        reg(Command("edit.cut", "edit.cut", "Edit",
                    lambda: self._ed("cut"), "Ctrl+X", keywords=["cut"]))
        reg(Command("edit.copy", "edit.copy", "Edit",
                    lambda: self._ed("copy"), "Ctrl+C", keywords=["copy"]))
        reg(Command("edit.paste", "edit.paste", "Edit",
                    lambda: self._ed("paste"), "Ctrl+V", keywords=["paste"]))
        reg(Command("edit.select_all", "edit.select_all", "Edit",
                    lambda: self._ed("selectAll"), "Ctrl+A",
                    keywords=["select", "all"]))
        reg(Command("edit.goto_line", "edit.goto_line", "Edit",
                    self.go_to_line, "Ctrl+G", keywords=["goto", "line", "go"]))
        
        # --- Поиск и замена ---
        reg(Command("edit.find", "edit.find", "Edit",
                    self.show_find, "Ctrl+F",
                    keywords=["find", "search"]))
        reg(Command("edit.replace", "edit.replace", "Edit",
                    self.show_replace, "Ctrl+H",
                    keywords=["replace", "find", "substitute"]))
        reg(Command("edit.find_next", "edit.find_next", "Edit",
                    lambda: self.find_panel.find_next(), "F3",
                    keywords=["find", "next"]))
        reg(Command("edit.find_prev", "edit.find_prev", "Edit",
                    lambda: self.find_panel.find_prev(), "Shift+F3",
                    keywords=["find", "previous"]))

        # --- Мультикурсор и Дата ---
        reg(Command(
            "edit.select_next", 
            "edit.select_next", 
            "Edit",
            lambda: self.current_editor() and self.current_editor().select_next_occurrence(),
            "Ctrl+D", 
            keywords=["select", "next", "occurrence", "multicursor"]
        ))
        
        reg(Command("edit.insert_date", "edit.insert_date", "Edit",
                    self.insert_datetime, "Ctrl+;",
                    keywords=["date", "time", "datetime", "insert"]))

        # --- View ---
        reg(Command("view.toggle_sidebar", "view.toggle_sidebar", "View",
                    self.toggle_sidebar, "Ctrl+B",
                    keywords=["sidebar", "toggle", "panel"]))
        reg(Command("view.font", "view.font", "View", self.change_font,
                    keywords=["font", "text", "size"]))
        reg(Command("view.zoom_in", "view.zoom_in", "View",
                    self.zoom_in, "Ctrl+=",
                    keywords=["zoom", "in", "bigger", "larger"]))
        reg(Command("view.zoom_out", "view.zoom_out", "View",
                    self.zoom_out, "Ctrl+-",
                    keywords=["zoom", "out", "smaller"]))
        reg(Command("view.zoom_reset", "view.zoom_reset", "View",
                    self.zoom_reset, "Ctrl+0",
                    keywords=["zoom", "reset", "default"]))

        reg(Command("palette.show", "palette.show", "View",
                    self.show_palette, "Ctrl+Shift+P",
                    keywords=["command", "palette", "commands"]))
        reg(Command("file.goto_file", "file.goto_file", "View",
                    self.show_file_finder, "Ctrl+P",
                    keywords=["goto", "file", "open", "quick", "finder"]))
        reg(Command("help.about", "help.about", "Help",
                    self.show_about, None,
                    keywords=["about", "version", "info"]))

    def _ed(self, method_name: str):
        ed = self.current_editor()
        if ed:
            getattr(ed, method_name)()

    # ============================================================
    #  МЕНЮ ИЗ КОМАНД
    # ============================================================
    def _build_menu_from_commands(self):
        menubar = self.menuBar()
        menubar.clear()

        categories_order = []
        by_cat = {}
        for cmd in self.commands.all():
            if cmd.category not in by_cat:
                by_cat[cmd.category] = []
                categories_order.append(cmd.category)
            by_cat[cmd.category].append(cmd)

        for cat in categories_order:
            if cat == "View":
                cmds = [c for c in by_cat[cat] if c.id != "palette.show"]
                menu = menubar.addMenu(tr(f"menu.{cat}"))
                for cmd in cmds:
                    self._add_action(menu, cmd)
                menu.addSeparator()

                # Подменю «Язык»
                lang_menu = menu.addMenu(tr("view.language"))
                current_lang = get_language()
                for lang_code, lang_name in LANGUAGES.items():
                    act = QAction(lang_name, self)
                    act.setCheckable(True)
                    act.setChecked(lang_code == current_lang)
                    act.triggered.connect(
                        lambda checked=False, code=lang_code: self._set_language(code)
                    )
                    lang_menu.addAction(act)

                menu.addSeparator()
                pal = self.commands.get("palette.show")
                if pal:
                    self._add_action(menu, pal).setMenuRole(QAction.NoRole)
            else:
                menu = menubar.addMenu(tr(f"menu.{cat}"))
                for cmd in by_cat[cat]:
                    self._add_action(menu, cmd)
                if cat == "File":
                    menu.addSeparator()
                    self._add_recent_submenu(menu)
                    menu.addSeparator()
                    
                    act = QAction(tr("file.autosave"), self)
                    act.setCheckable(True)
                    act.setChecked(self.autosave_enabled)
                    act.triggered.connect(self.toggle_autosave)
                    menu.addAction(act)

                    act2 = QAction(tr("file.utf8_bom"), self)
                    act2.setCheckable(True)
                    act2.setChecked(self.utf8_bom_enabled)
                    act2.triggered.connect(self.toggle_utf8_bom)
                    menu.addAction(act2)

    def _add_recent_submenu(self, parent_menu):
        recent_menu = parent_menu.addMenu(tr("file.open_recent"))
        if not self._recent:
            act = QAction(tr("file.no_recent"), self)
            act.setEnabled(False)
            recent_menu.addAction(act)
            return
        for path in self._recent:
            label = f"{os.path.basename(path)}  —  {os.path.dirname(path)}"
            act = QAction(label, self)
            act.setToolTip(path)
            act.triggered.connect(lambda checked=False, p=path: self.open_path(p))
            recent_menu.addAction(act)
        recent_menu.addSeparator()
        clear_act = QAction(tr("file.clear_recent"), self)
        clear_act.triggered.connect(self._clear_recent)
        recent_menu.addAction(clear_act)

    def _clear_recent(self):
        clear_recent()
        self._recent = []
        self._build_menu_from_commands()
        self.status.showMessage(tr("file.no_recent"), 2000)

    def _set_language(self, lang: str):
        set_language(lang)
        self.cfg["language"] = lang
        save_config(self.cfg)
        self._build_menu_from_commands()
        self._refresh_ui_texts()
        self.update_status()

    def _refresh_ui_texts(self):
        self.file_tree.btn_open.setText(tr("ui.open_folder"))
        self.palette.input.setPlaceholderText(tr("ui.palette_placeholder"))
        self.file_finder.input.setPlaceholderText(tr("ui.finder_placeholder"))
        self.find_panel.input_find.setPlaceholderText(tr("ui.search_placeholder"))
        self.find_panel.input_replace.setPlaceholderText(tr("ui.replace_placeholder"))
        self.find_panel.btn_replace.setText(tr("ui.replace_one"))
        self.find_panel.btn_replace_all.setText(tr("ui.replace_all"))

    def _add_action(self, menu, cmd: Command) -> QAction:
        action = QAction(cmd.title, self)
        if cmd.shortcut:
            action.setShortcut(QKeySequence(cmd.shortcut))
            action.setShortcutContext(Qt.WindowShortcut)
            action.setText(f"{cmd.title}\t{cmd.shortcut}")
        action.triggered.connect(lambda checked=False, cid=cmd.id:
                                 self.commands.execute(cid))
        menu.addAction(action)
        return action

    # ============================================================
    #  ПАЛИТРА И FINDER
    # ============================================================
    def show_palette(self):
        self.palette.refresh("")
        self.palette.input.clear()
        self.palette.show_centered()

    def show_file_finder(self):
        root = self.file_tree.current_folder()
        self.file_finder.set_root(root)
        self.file_finder.show_centered()

    def _on_project_folder_changed(self, path: str):
        finder = getattr(self, "file_finder", None)
        if finder is not None:
            finder.set_root(path)

    def show_find(self):
        self.find_panel.show_find()

    def show_replace(self):
        self.find_panel.show_replace()

    # ============================================================
    #  ФАЙЛЫ
    # ============================================================
    def current_editor(self):
        return self.tabs.currentWidget()

    def new_file(self):
        editor = CodeEditor()
        PygmentsHighlighter(editor.document(), "text")
        editor._spell_checker = SpellChecker(editor.document(), "ru_RU")
        editor.setProperty("path", None)

        idx = self.tabs.addTab(editor, tr("ui.untitled"))
        self.tabs.setCurrentIndex(idx)
        editor.document().modificationChanged.connect(self.update_title)
        editor.cursorPositionChanged.connect(self.update_status)
        editor.textChanged.connect(self._on_editor_modified)
        self.update_title()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("file.open"))
        if path:
            self.open_path(path)

    def open_path(self, path):
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            if ed.property("path") == path:
                self.tabs.setCurrentIndex(i)
                return

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="cp1251") as f:
                    text = f.read()
            except Exception as e:
                QMessageBox.critical(self, tr("ui.error"),
                                     tr("ui.cant_read", e=str(e)))
                return
        except Exception as e:
            QMessageBox.critical(self, tr("ui.error"), str(e))
            return

        editor = CodeEditor()
        editor.setPlainText(text)
        editor.setProperty("path", path)
        lang = self._detect_language(path)
        PygmentsHighlighter(editor.document(), lang)
        editor._spell_checker = SpellChecker(editor.document(), "ru_RU")
        
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(self.update_title)
        editor.cursorPositionChanged.connect(self.update_status)
        editor.textChanged.connect(self._on_editor_modified)

        idx = self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setCurrentIndex(idx)
        self.update_title()

        self._recent = add_recent(path)
        self._build_menu_from_commands()

    def save_file(self):
        editor = self.current_editor()
        if not editor:
            return
        path = editor.property("path")
        if not path:
            self.save_file_as()
            return
        self._write_to(editor, path)

    def save_file_as(self):
        editor = self.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("file.save_as"))
        if not path:
            return
        self._write_to(editor, path)

    def _write_to(self, editor, path):
        try:
            with self._open_for_write(path) as f:
                f.write(editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, tr("ui.error"), str(e))
            return
        editor.setProperty("path", path)
        editor.document().setModified(False)
        idx = self.tabs.indexOf(editor)
        self.tabs.setTabText(idx, os.path.basename(path))
        self.update_title()

    def _open_for_write(self, path):
        if self.utf8_bom_enabled:
            return open(path, "w", encoding="utf-8-sig")
        return open(path, "w", encoding="utf-8")

    def close_tab(self, index):
        if index < 0:
            return
        editor = self.tabs.widget(index)
        if editor.document().isModified():
            name = self.tabs.tabText(index)
            res = QMessageBox.question(
                self, tr("ui.unsaved_title"),
                tr("ui.unsaved_message", name=name),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if res == QMessageBox.Cancel:
                return
            if res == QMessageBox.Save:
                self.tabs.setCurrentIndex(index)
                self.save_file()
                if editor.document().isModified():
                    return
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.new_file()

    # ============================================================
    #  ИНТЕРФЕЙС И НАСТРОЙКИ
    # ============================================================
    def update_title(self):
        editor = self.current_editor()
        if not editor:
            self.setWindowTitle(tr("ui.app_name"))
            return
        path = editor.property("path") or tr("ui.untitled")
        mod = "•" if editor.document().isModified() else ""
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.tabs.setTabText(idx, f"{mod}{os.path.basename(path)}")
        self.setWindowTitle(f"{path} {mod} — {tr('ui.app_name')}")

    def update_status(self):
        editor = self.current_editor()
        if not editor:
            return
        cur = editor.textCursor()
        line = cur.blockNumber() + 1
        col = cur.columnNumber() + 1
        self.status.showMessage(tr("ui.status_position", line=line, col=col))

    def toggle_sidebar(self):
        self.file_tree.setVisible(not self.file_tree.isVisible())

    def show_about(self):
        from PySide6.QtWidgets import QMessageBox
        text = tr("about.text", version=__version__)
        QMessageBox.about(self, tr("about.title"), text)

    def go_to_line(self):
        editor = self.current_editor()
        if not editor:
            return
        total = editor.blockCount()
        n, ok = QInputDialog.getInt(
            self, tr("ui.goto_line_title"),
            tr("ui.goto_line_prompt", total=total),
            1, 1, total
        )
        if not ok:
            return
        cursor = QTextCursor(editor.document().findBlockByNumber(n - 1))
        editor.setTextCursor(cursor)
        editor.centerCursor()

    def insert_datetime(self):
        from datetime import datetime
        ed = self.current_editor()
        if not ed:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ed.insertPlainText(now)

    def change_font(self):
        editor = self.current_editor()
        if not editor:
            return
        font, ok = QFontDialog.getFont(editor.font(), self)
        if ok:
            for i in range(self.tabs.count()):
                self.tabs.widget(i).setFont(font)

    def toggle_autosave(self):
        self.autosave_enabled = not self.autosave_enabled
        self.cfg["autosave"] = self.autosave_enabled
        save_config(self.cfg)
        self._build_menu_from_commands()
        key = "ui.autosave_on" if self.autosave_enabled else "ui.autosave_off"
        self.status.showMessage(tr(key), 2000)

    def toggle_utf8_bom(self):
        self.utf8_bom_enabled = not self.utf8_bom_enabled
        self.cfg["utf8_bom"] = self.utf8_bom_enabled
        save_config(self.cfg)
        self._build_menu_from_commands()
        key = "ui.bom_on" if self.utf8_bom_enabled else "ui.bom_off"
        self.status.showMessage(tr(key), 2000)

    def _on_editor_modified(self):
        if not self.autosave_enabled:
            return
        self._autosave_timer.start()

    def _do_autosave(self):
        ed = self.current_editor()
        if not ed:
            return
        path = ed.property("path")
        if not path:
            return
        if not ed.document().isModified():
            return
        try:
            with self._open_for_write(path) as f:
                f.write(ed.toPlainText())
        except Exception as e:
            print(f"[autosave] {e}")
            return
        ed.document().setModified(False)
        self.status.showMessage(tr("ui.saved"), 2000)

    def zoom_in(self):
        self._zoom(+1)

    def zoom_out(self):
        self._zoom(-1)

    def zoom_reset(self):
        self._apply_font_size(11)

    def _zoom(self, delta: int):
        ed = self.current_editor()
        if not ed:
            return
        current = ed.font().pointSize()
        if current <= 0:
            current = 11
        self._apply_font_size(current + delta)

    def _apply_font_size(self, size: int):
        size = max(6, min(size, 72))
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            font = ed.font()
            font.setPointSize(size)
            ed.setFont(font)
            ed.update_line_number_area_width(0)
            ed.setTabStopDistance(4 * ed.fontMetrics().horizontalAdvance(' '))

    # ============================================================
    #  СЕССИЯ И ЯЗЫК
    # ============================================================
    def closeEvent(self, event):
        self._save_session_now()
        super().closeEvent(event)

    def _save_session_now(self):
        open_files = []
        cursor_positions = {}
        active_index = -1

        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i)
            path = ed.property("path")
            if path:
                open_files.append(path)
                cursor_positions[path] = ed.textCursor().position()
                if i == self.tabs.currentIndex():
                    active_index = len(open_files) - 1

        data = {
            "project_folder": self.file_tree.current_folder() or "",
            "open_files": open_files,
            "active_index": active_index,
            "window_geometry": bytes(self.saveGeometry().toBase64()).decode("ascii"),
            "splitter_sizes": self.splitter.sizes(),
            "cursor_positions": cursor_positions,
        }
        save_session(data)

    def _restore_session(self, session: dict):
        geom = session.get("window_geometry")
        if geom:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geom.encode("ascii")))
            except Exception:
                pass

        sizes = session.get("splitter_sizes")
        if sizes and len(sizes) == 2:
            self.splitter.setSizes(sizes)

        folder = session.get("project_folder")
        if folder and os.path.isdir(folder):
            self.file_tree.open_folder(folder)
        else:
            self.file_tree.open_folder(QDir.homePath())

        files = session.get("open_files", [])
        cursor_positions = session.get("cursor_positions", {})
        opened_any = False
        for path in files:
            if os.path.isfile(path):
                self.open_path(path)
                opened_any = True
                pos = cursor_positions.get(path)
                if pos is not None:
                    ed = self.tabs.currentWidget()
                    if ed:
                        cur = ed.textCursor()
                        cur.setPosition(min(pos, len(ed.toPlainText())))
                        ed.setTextCursor(cur)

        if not opened_any:
            self.new_file()

        active = session.get("active_index", -1)
        if 0 <= active < self.tabs.count():
            self.tabs.setCurrentIndex(active)

    def _detect_language(self, path: str) -> str:
        if not path:
            return "text"
        ext = os.path.splitext(path)[1].lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".sql": "sql",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".java": "java",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sh": "bash",
            ".bat": "batch",
            ".ps1": "powershell",
            ".txt": "text",
        }
        return mapping.get(ext, "text")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.find_panel.isVisible():
            self.find_panel.hide_panel()
            return
        super().keyPressEvent(event)