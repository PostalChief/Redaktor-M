from PySide6.QtWidgets import QWidget, QPlainTextEdit
from PySide6.QtGui import QPainter, QColor, QTextBlock, QPolygon
from PySide6.QtCore import Qt, QRect, QSize, QPoint


class FoldArea(QWidget):
    """Область слева (между номерами строк и кодом), где рисуются треугольники."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(16, 0)

    def paintEvent(self, event):
        self.editor.fold_area_paint_event(event)

    def mousePressEvent(self, event):
        self.editor.fold_area_mouse_press(event)


class FoldingMixin:
    """
    Миксин для CodeEditor, добавляющий свёртку кода.
    Мы будем подмешивать его в класс CodeEditor.
    """
    def init_folding(self):
        self.fold_area = FoldArea(self)
        self.folded_blocks = set()  # Храним номера строк, которые свёрнуты
        
        # Переопределяем обновление отступов, чтобы учесть новую область
        self.setViewportMargins(self.line_number_area_width() + 16, 0, 0, 0)
        
    def update_fold_area_geometry(self):
        cr = self.contentsRect()
        self.fold_area.setGeometry(
            QRect(cr.left() + self.line_number_area_width(), cr.top(), 16, cr.height())
        )

    def fold_area_paint_event(self, event):
        painter = QPainter(self.fold_area)
        painter.fillRect(event.rect(), QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # Определяем, есть ли блок для свёртки
                indent = self.block_indent(block)
                next_block = block.next()
                
                # Если следующая строка имеет больший отступ — это начало блока
                if next_block.isValid() and self.block_indent(next_block) > indent:
                    # Рисуем треугольник
                    is_folded = block_number in self.folded_blocks
                    self.draw_triangle(painter, int(top), is_folded)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def draw_triangle(self, painter, top, is_folded):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#d4d4d4"))
        
        y_center = top + self.fontMetrics().height() // 2
        x_center = 8

        if is_folded:
            # Треугольник вправо (▶)
            points = [
                QPoint(x_center - 3, y_center - 4),
                QPoint(x_center - 3, y_center + 4),
                QPoint(x_center + 4, y_center),
            ]
        else:
            # Треугольник вниз (▼)
            points = [
                QPoint(x_center - 4, y_center - 3),
                QPoint(x_center + 4, y_center - 3),
                QPoint(x_center, y_center + 4),
            ]
        painter.drawPolygon(QPolygon(points))

    def fold_area_mouse_press(self, event):
        x = event.position().x()
        y = event.position().y()
        
        # Находим, по какой строке кликнули
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= y:
            if block.isVisible() and bottom >= y:
                # Проверяем, есть ли у этого блока что сворачивать
                indent = self.block_indent(block)
                next_block = block.next()
                
                if next_block.isValid() and self.block_indent(next_block) > indent:
                    self.toggle_fold(block_number)
                break

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def block_indent(self, block):
        """Считает количество пробелов в начале строки."""
        text = block.text()
        return len(text) - len(text.lstrip())

    def toggle_fold(self, block_number):
        """Сворачивает или разворачивает блок."""
        if block_number in self.folded_blocks:
            self.folded_blocks.remove(block_number)
            self.unfold_block(block_number)
        else:
            self.folded_blocks.add(block_number)
            self.fold_block(block_number)
        
        self.fold_area.update()
        self.viewport().update()

    def fold_block(self, block_number):
        """Скрывает строки, которые относятся к блоку."""
        start_block = self.document().findBlockByNumber(block_number)
        indent = self.block_indent(start_block)
        
        block = start_block.next()
        while block.isValid():
            if self.block_indent(block) <= indent and block.text().strip() != "":
                break
            block.setVisible(False)
            block = block.next()
        
        self.document().markContentsDirty(start_block.position(), self.document().characterCount())

    def unfold_block(self, block_number):
        """Показывает скрытые строки."""
        start_block = self.document().findBlockByNumber(block_number)
        indent = self.block_indent(start_block)
        
        block = start_block.next()
        while block.isValid():
            if self.block_indent(block) <= indent and block.text().strip() != "":
                break
            block.setVisible(True)
            block = block.next()
        
        self.document().markContentsDirty(start_block.position(), self.document().characterCount())