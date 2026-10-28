from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import QRect, QSize


class Minimap(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(80)
        self.font = QFont("Consolas", 2)
        self.line_height = 3
        
        self.bg_color = QColor("#1e1e1e")
        self.text_color = QColor("#555555")
        self.viewport_color = QColor("#2a2d2e")

    def sizeHint(self):
        return QSize(80, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.bg_color)
        
        doc = self.editor.document()
        block = doc.firstBlock()
        
        painter.setPen(self.text_color)
        painter.setFont(self.font)
        
        y = 0
        while block.isValid() and y < self.height():
            text = block.text().strip()
            if text:
                painter.drawText(4, y + self.line_height, text[:100])
            
            block = block.next()
            y += self.line_height
            
            if y > doc.blockCount() * self.line_height:
                break

        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() > 0:
            scroll_ratio = scrollbar.value() / scrollbar.maximum()
            visible_lines = self.editor.viewport().height() // self.editor.fontMetrics().height()
            total_lines = doc.blockCount()
            
            if total_lines > 0:
                viewport_height = int((visible_lines / total_lines) * self.height())
                viewport_y = int(scroll_ratio * (self.height() - viewport_height))
                
                self.viewport_color.setAlpha(80)
                painter.fillRect(0, viewport_y, self.width(), viewport_height, self.viewport_color)

    def mousePressEvent(self, event):
        click_y = event.position().y()
        ratio = click_y / self.height()
        
        scrollbar = self.editor.verticalScrollBar()
        target_value = int(ratio * scrollbar.maximum())
        scrollbar.setValue(target_value)