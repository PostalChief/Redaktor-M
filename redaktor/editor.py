from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtCore import Qt, QRect, QSize, QTimer

from .folding import FoldingMixin
from .minimap import Minimap
from .completer import CodeCompleter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit, FoldingMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.line_number_bg = "#252526"
        self.line_number_color = "#858585"
        
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        font = QFont("Monospace", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        self._last_found_cursor = None

        # Стили
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                border: none;
            }
        """)
        
        # Инициализация миникарты
        self.minimap = Minimap(self)
        
        # Инициализация автодополнения
        self.completer = CodeCompleter(self)
        self.completer.setWidget(self)
        self.completer.popup().setStyleSheet("""
            QListView {
                background: #252526; color: #d4d4d4;
                border: 1px solid #454545;
                selection-background-color: #094771;
            }
        """)
        
        # Таймер для обновления словаря автодополнения
        self._completer_timer = QTimer()
        self._completer_timer.setSingleShot(True)
        self._completer_timer.setInterval(500) # 0.5 сек после последнего нажатия
        self._completer_timer.timeout.connect(self._update_completer_words)
        self.textChanged.connect(self._completer_timer.start)
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.init_folding()

    def _update_completer_words(self):
        """Собирает слова из текста для автодополнения (с задержкой)."""
        if hasattr(self, 'completer'):
            self.completer.update_words(self.toPlainText())

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width() + 16, 0, 80, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                         self.line_number_area.width(), rect.height())
        
        if hasattr(self, 'fold_area'):
            if dy:
                self.fold_area.scroll(0, dy)
            else:
                self.fold_area.update(0, rect.y(), self.fold_area.width(), rect.height())
                
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
        if hasattr(self, 'minimap'):
            self.minimap.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(),
                  self.line_number_area_width(), cr.height())
        )
        self.update_fold_area_geometry()
        
        if hasattr(self, 'minimap'):
            self.minimap.setGeometry(
                QRect(cr.right() - 80, cr.top(), 80, cr.height())
            )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.line_number_bg))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(QColor(self.line_number_color))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, int(top),
                    self.line_number_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2a2d2e"))
            sel.format.setProperty(QTextCharFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    def apply_theme(self, theme: dict):
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {theme['editor_bg']};
                color: {theme['text_color']};
                selection-background-color: {theme['selection_bg']};
                border: none;
            }}
        """)
        self.viewport().setStyleSheet(f"background-color: {theme['editor_bg']};")
        self.line_number_bg = theme['line_number_bg']
        self.line_number_color = theme['line_number_color']
        self.update()
        self.line_number_area.update()

    def _text_under_cursor(self):
        cursor = self.textCursor()
        block_text = cursor.block().text()
        pos_in_block = cursor.positionInBlock()
        
        start = pos_in_block
        while start > 0 and (block_text[start - 1].isalnum() or block_text[start - 1] == "_"):
            start -= 1
            
        return block_text[start:pos_in_block]

    def keyPressEvent(self, event):
        # --- Умный отступ по Enter ---
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            
            # Получаем отступ текущей строки
            indent = ""
            for char in text:
                if char in (" ", "\t"):
                    indent += char
                else:
                    break
            
            # Проверяем, надо ли увеличить отступ
            stripped_text = text.strip()
            if stripped_text.endswith(":") or stripped_text.endswith("{"):
                indent += "    "  # Добавляем 4 пробела
                
            # Вставляем перенос строки и отступ
            cursor.insertText("\n" + indent)
            self.setTextCursor(cursor)
            return
        # --- Автодополнение ---
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        if event.text() and (event.text().isalnum() or event.text() == "_"):
            super().keyPressEvent(event)
            
            prefix = self._text_under_cursor()
            if prefix and len(prefix) >= 2:
                self.completer.setCompletionPrefix(prefix)
                if self.completer.completionCount() > 0:
                    rect = self.cursorRect()
                    rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                                  self.completer.popup().verticalScrollBar().sizeHint().width() + 20)
                    self.completer.complete(rect)
            else:
                self.completer.popup().hide()
            return

        # --- Tab и Shift+Tab ---
        if event.key() == Qt.Key_Tab and not event.modifiers():
            self._indent_selection()
            return
        if event.key() == Qt.Key_Backtab:
            self._unindent_selection()
            return

        # --- Автозакрытие скобок ---
        pairs = {
            "(": ")", "[": "]", "{": "}",
            '"': '"', "'": "'",
        }
        text = event.text()
        if text in pairs:
            cursor = self.textCursor()
            closing = pairs[text]
            if cursor.hasSelection():
                selected = cursor.selectedText()
                cursor.insertText(f"{text}{selected}{closing}")
            else:
                cursor.insertText(f"{text}{closing}")
                new_cursor = self.textCursor()
                new_cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(new_cursor)
            return

        if text in pairs.values():
            cursor = self.textCursor()
            if cursor.position() < self.document().characterCount():
                next_char = self.document().characterAt(cursor.position())
                if next_char == text:
                    new_cursor = self.textCursor()
                    new_cursor.movePosition(QTextCursor.NextCharacter)
                    self.setTextCursor(new_cursor)
                    return

        super().keyPressEvent(event)

    def _indent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.insertText("    ")
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        
        cursor.beginEditBlock()
        block = start_block
        while block.isValid():
            block_cursor = QTextCursor(block)
            block_cursor.movePosition(QTextCursor.StartOfBlock)
            block_cursor.insertText("    ")
            if block == end_block:
                break
            block = block.next()
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _unindent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            block = cursor.block()
            text = block.text()
            pos_in_block = cursor.positionInBlock()
            if text[:pos_in_block].endswith("    "):
                for _ in range(4):
                    cursor.deletePreviousChar()
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        
        cursor.beginEditBlock()
        block = start_block
        while block.isValid():
            block_cursor = QTextCursor(block)
            block_cursor.movePosition(QTextCursor.StartOfBlock)
            text = block.text()
            if text.startswith("    "):
                block_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                block_cursor.removeSelectedText()
            elif text.startswith("\t"):
                block_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                block_cursor.removeSelectedText()
            elif text.startswith(" "):
                block_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                block_cursor.removeSelectedText()
            
            if block == end_block:
                break
            block = block.next()
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def select_next_occurrence(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)
            self._last_found_cursor = cursor
            return

        selected_text = cursor.selectedText()
        if not selected_text:
            return

        doc = self.document()
        search_from = self._last_found_cursor if self._last_found_cursor else cursor
        found = doc.find(selected_text, search_from)

        if not found.isNull():
            sel = QTextEdit.ExtraSelection()
            sel.cursor = found
            sel.format.setBackground(QColor("#264f78"))

            extras = self.extraSelections()
            already_exists = False
            for ex in extras:
                if ex.cursor.position() == found.position() and ex.cursor.hasSelection():
                    already_exists = True
                    break

            if not already_exists:
                extras.append(sel)
                self.setExtraSelections(extras)
                self._last_found_cursor = found