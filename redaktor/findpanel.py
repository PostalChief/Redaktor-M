from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QCheckBox, QToolButton, QTextEdit
)
from PySide6.QtGui import QTextDocument, QTextCursor, QColor, QTextCharFormat
from PySide6.QtCore import Qt, Signal, QRegularExpression


class FindPanel(QWidget):
    """
    Панель поиска/замены внизу окна.
    Управляется через show_find() / show_replace() / hide_panel().
    """

    closed = Signal()

    def __init__(self, editor_provider, parent=None):
        """
        editor_provider — функция без аргументов, возвращающая текущий CodeEditor.
        Это позволяет панели всегда работать с активной вкладкой.
        """
        super().__init__(parent)
        self.get_editor = editor_provider
        self._build_ui()
        self.hide()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(4)

        # ---------- Строка 1: Найти ----------
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self.btn_toggle_replace = QToolButton()
        self.btn_toggle_replace.setText("▸")
        self.btn_toggle_replace.setToolTip("Развернуть замену")
        self.btn_toggle_replace.setCheckable(True)
        self.btn_toggle_replace.clicked.connect(self._toggle_replace)
        row1.addWidget(self.btn_toggle_replace)

        self.input_find = QLineEdit()
        self.input_find.setPlaceholderText("Найти")
        self.input_find.textChanged.connect(self._on_find_text_changed)
        self.input_find.returnPressed.connect(self.find_next)
        row1.addWidget(self.input_find, 1)

        self.lbl_counter = QLabel("")
        self.lbl_counter.setMinimumWidth(90)
        self.lbl_counter.setAlignment(Qt.AlignCenter)
        self.lbl_counter.setStyleSheet("color: #858585;")
        row1.addWidget(self.lbl_counter)

        self.btn_prev = QPushButton("▲")
        self.btn_prev.setToolTip("Найти назад (Shift+F3)")
        self.btn_prev.setFixedWidth(32)
        self.btn_prev.clicked.connect(self.find_prev)
        row1.addWidget(self.btn_prev)

        self.btn_next = QPushButton("▼")
        self.btn_next.setToolTip("Найти далее (F3)")
        self.btn_next.setFixedWidth(32)
        self.btn_next.clicked.connect(self.find_next)
        row1.addWidget(self.btn_next)

        self.chk_case = QCheckBox("Aa")
        self.chk_case.setToolTip("Учитывать регистр")
        self.chk_case.stateChanged.connect(self._on_find_text_changed)
        row1.addWidget(self.chk_case)

        self.chk_word = QCheckBox("ab")
        self.chk_word.setToolTip("Только слово целиком")
        self.chk_word.stateChanged.connect(self._on_find_text_changed)
        row1.addWidget(self.chk_word)

        self.chk_regex = QCheckBox(".*")
        self.chk_regex.setToolTip("Регулярное выражение")
        self.chk_regex.stateChanged.connect(self._on_find_text_changed)
        row1.addWidget(self.chk_regex)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Закрыть (Esc)")
        self.btn_close.setFixedWidth(32)
        self.btn_close.clicked.connect(self.hide_panel)
        row1.addWidget(self.btn_close)

        root.addLayout(row1)

        # ---------- Строка 2: Заменить (скрыта по умолчанию) ----------
        self.row2_widget = QWidget()
        row2 = QHBoxLayout(self.row2_widget)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(4)

        spacer = QWidget()
        spacer.setFixedWidth(24)
        row2.addWidget(spacer)

        self.input_replace = QLineEdit()
        self.input_replace.setPlaceholderText("Заменить на")
        self.input_replace.returnPressed.connect(self.replace_one)
        row2.addWidget(self.input_replace, 1)

        self.btn_replace = QPushButton("Заменить")
        self.btn_replace.clicked.connect(self.replace_one)
        row2.addWidget(self.btn_replace)

        self.btn_replace_all = QPushButton("Заменить всё")
        self.btn_replace_all.clicked.connect(self.replace_all)
        row2.addWidget(self.btn_replace_all)

        root.addWidget(self.row2_widget)
        self.row2_widget.hide()

        self.setStyleSheet("""
            FindPanel {
                background: #252526;
                border-top: 1px solid #3c3c3c;
            }
            QLineEdit {
                background: #3c3c3c; color: #d4d4d4;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px;
            }
            QLineEdit:focus { border: 1px solid #007acc; }
            QPushButton {
                background: #3c3c3c; color: #d4d4d4;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover { background: #4a4a4a; }
            QToolButton {
                background: transparent; color: #d4d4d4;
                border: none; padding: 4px;
            }
            QCheckBox { color: #d4d4d4; }
            QLabel { color: #858585; }
        """)

    # ============================================================
    #  ПОКАЗ / СКРЫТИЕ
    # ============================================================
    def show_find(self):
        """Ctrl+F — открыть панель в режиме поиска."""
        self.row2_widget.hide()
        self.btn_toggle_replace.setChecked(False)
        self.btn_toggle_replace.setText("▸")
        self._show_and_focus(self.input_find)

    def show_replace(self):
        """Ctrl+H — открыть панель в режиме замены."""
        self.row2_widget.show()
        self.btn_toggle_replace.setChecked(True)
        self.btn_toggle_replace.setText("▾")
        self._show_and_focus(self.input_find)

    def hide_panel(self):
        """Esc или крестик — скрыть панель и вернуть фокус в редактор."""
        self.hide()
        ed = self.get_editor()
        if ed:
            ed.setFocus()
        self.closed.emit()

    def _show_and_focus(self, widget):
        self.show()
        widget.setFocus()
        widget.selectAll()
        # Если в редакторе есть выделение — подставим его в поле поиска
        ed = self.get_editor()
        if ed:
            cursor = ed.textCursor()
            if cursor.hasSelection():
                text = cursor.selectedText()
                if "\u2029" not in text:  # не многострочное
                    self.input_find.setText(text)

    def _toggle_replace(self):
        visible = self.btn_toggle_replace.isChecked()
        self.row2_widget.setVisible(visible)
        self.btn_toggle_replace.setText("▾" if visible else "▸")

    # ============================================================
    #  ПОИСК
    # ============================================================
    def _flags(self):
        flags = QTextDocument.FindFlags()
        if self.chk_case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.chk_word.isChecked():
            flags |= QTextDocument.FindWholeWords
        return flags

    def _on_find_text_changed(self):
        self._update_counter()

    def _build_pattern(self, needle: str) -> QRegularExpression:
        """Собирает QRegularExpression из строки + галочек."""
        if self.chk_regex.isChecked():
            pattern = QRegularExpression(needle)
        else:
            esc = QRegularExpression.escape(needle)
            if self.chk_word.isChecked():
                esc = rf"\b{esc}\b"
            pattern = QRegularExpression(esc)
        if not self.chk_case.isChecked():
            pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
        return pattern

    def _update_counter(self):
        """Обновляет метку 'X из Y' и подсвечивает все совпадения."""
        ed = self.get_editor()
        if not ed:
            self.lbl_counter.setText("")
            return

        needle = self.input_find.text()
        if not needle:
            self.lbl_counter.setText("")
            # Вернём только подсветку текущей строки
            ed.highlight_current_line()
            return

        doc = ed.document()
        pattern = self._build_pattern(needle)
        if not pattern.isValid():
            self.lbl_counter.setText("Regex?")
            self.lbl_counter.setStyleSheet("color: #f48771;")
            return

        matches = []
        it = pattern.globalMatch(doc.toPlainText())
        while it.hasNext():
            m = it.next()
            cur = QTextCursor(doc)
            cur.setPosition(m.capturedStart())
            cur.setPosition(m.capturedEnd(), QTextCursor.KeepAnchor)
            matches.append(cur)

        selections = []

        # Подсветка текущей строки (первой)
        if not ed.isReadOnly():
            cur_line = QTextEdit.ExtraSelection()
            cur_line.format.setBackground(QColor("#2a2d2e"))
            cur_line.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            cur_line.cursor = ed.textCursor()
            cur_line.cursor.clearSelection()
            selections.append(cur_line)

        # Все совпадения — жёлтым
        for cur in matches:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cur
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#4a4a00"))
            sel.format = fmt
            selections.append(sel)

        # Текущее совпадение — синим
        current_idx = -1
        cur_pos = ed.textCursor().position()
        for i, m in enumerate(matches):
            if m.selectionStart() <= cur_pos <= m.selectionEnd():
                current_idx = i
                break

        if current_idx >= 0:
            sel = QTextEdit.ExtraSelection()
            sel.cursor = matches[current_idx]
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#007acc"))
            fmt.setForeground(QColor("#ffffff"))
            sel.format = fmt
            selections.append(sel)

        ed.setExtraSelections(selections)

        total = len(matches)
        if total == 0:
            self.lbl_counter.setText("Нет совпадений")
            self.lbl_counter.setStyleSheet("color: #f48771;")
        else:
            if current_idx >= 0:
                self.lbl_counter.setText(f"{current_idx + 1} из {total}")
            else:
                self.lbl_counter.setText(f"{total} совпад.")
            self.lbl_counter.setStyleSheet("color: #858585;")

    def find_next(self):
        self._find(direction=1)

    def find_prev(self):
        self._find(direction=-1)

    def _find(self, direction: int):
        ed = self.get_editor()
        if not ed:
            return
        needle = self.input_find.text()
        if not needle:
            return

        pattern = self._build_pattern(needle)
        if not pattern.isValid():
            return

        flags = QTextDocument.FindFlags()
        if direction == -1:
            flags |= QTextDocument.FindBackward

        found = ed.document().find(pattern, ed.textCursor(), flags)

        if found.isNull():
            # Заворачиваем поиск к началу/концу
            cur = QTextCursor(ed.document())
            if direction == -1:
                cur.movePosition(QTextCursor.End)
            else:
                cur.movePosition(QTextCursor.Start)
            found = ed.document().find(pattern, cur, flags)

        if not found.isNull():
            ed.setTextCursor(found)
            ed.centerCursor()
            self._update_counter()

    # ============================================================
    #  ЗАМЕНА
    # ============================================================
    def replace_one(self):
        ed = self.get_editor()
        if not ed:
            return
        cursor = ed.textCursor()
        needle = self.input_find.text()
        if not needle:
            return

        selected = cursor.selectedText()
        if selected and self._matches(selected, needle):
            cursor.insertText(self.input_replace.text())
            self._update_counter()

        self.find_next()

    def replace_all(self):
        ed = self.get_editor()
        if not ed:
            return
        needle = self.input_find.text()
        replacement = self.input_replace.text()
        if not needle:
            return

        pattern = self._build_pattern(needle)
        if not pattern.isValid():
            return

        cursor = QTextCursor(ed.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        count = 0
        while True:
            found = ed.document().find(pattern, cursor)
            if found.isNull():
                break
            found.insertText(replacement)
            cursor = found
            count += 1
        cursor.endEditBlock()
        self._update_counter()

    def _matches(self, text: str, needle: str) -> bool:
        pattern = self._build_pattern(needle)
        if not pattern.isValid():
            return False
        return pattern.match(text).hasMatch()