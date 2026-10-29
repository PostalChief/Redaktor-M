from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtCore import Qt, QRect, QSize

from .folding import FoldingMixin
from .minimap import Minimap


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

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                border: none;
            }
        """)
        
        self.minimap = Minimap(self)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.init_folding()

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

    def keyPressEvent(self, event):
        # --- 1. Обработка Tab и Shift+Tab ---
        if event.key() == Qt.Key_Tab and not event.modifiers():
            self._indent_selection()
            return
        if event.key() == Qt.Key_Backtab:  # Backtab — это Shift+Tab
            self._unindent_selection()
            return

        # --- 2. Автозакрытие скобок ---
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
        """Сдвигает выделенный блок вправо на 4 пробела."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            # Если ничего не выделено — вставляем таб (4 пробела)
            cursor.insertText("    ")
            return

        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        # Находим начальную и конечную строки
        start_block = self.document().findBlock(start)
        end_block = self.document().findBlock(end)
        
        # Начинаем редактирование (для Undo)
        cursor.beginEditBlock()
        
        block = start_block
        while block.isValid():
            # Ставим курсор в начало строки
            block_cursor = QTextCursor(block)
            block_cursor.movePosition(QTextCursor.StartOfBlock)
            # Вставляем пробелы
            block_cursor.insertText("    ")
            
            if block == end_block:
                break
            block = block.next()
            
        cursor.endEditBlock()
        self.setTextCursor(cursor) # Возвращаем выделение

    def _unindent_selection(self):
        """Сдвигает выделенный блок влево (убирает 4 пробела)."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            # Если ничего не выделено, пытаемся удалить пробелы перед курсором
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
            # Проверяем, есть ли в начале строки пробелы для удаления
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