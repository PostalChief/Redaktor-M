from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PySide6.QtGui import QColor, QFont, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtCore import Qt, QRect, QSize

from .folding import FoldingMixin


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
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Переменная для хранения последнего найденного вхождения (Ctrl+D)
        self._last_found_cursor = None

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                border: none;
            }
        """)
        
        # Инициализация номеров строк
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Инициализация свёртки кода (Folding)
        self.init_folding()

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width() + 16, 0, 0, 0)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(),
                  self.line_number_area_width(), cr.height())
        )
        self.update_fold_area_geometry()

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(QColor("#858585"))
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

    # ============================================================
    #  АВТОЗАКРЫТИЕ СКОБОК И КАВЫЧЕК
    # ============================================================
    def keyPressEvent(self, event):
        pairs = {
            "(": ")",
            "[": "]",
            "{": "}",
            '"': '"',
            "'": "'",
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

    # ============================================================
    #  МУЛЬТИКУРСОРЫ (CTRL+D)
    # ============================================================
    def select_next_occurrence(self):
        """Выделяет следующее вхождение текущего слова (Ctrl+D)."""
        cursor = self.textCursor()

        # Если ничего не выделено — выделяем слово под курсором
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)
            self._last_found_cursor = cursor
            return

        selected_text = cursor.selectedText()
        if not selected_text:
            return

        # Ищем следующее вхождение (начиная с последнего найденного)
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