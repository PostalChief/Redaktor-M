from PySide6.QtWidgets import (
    QApplication, QDialog, QLineEdit, QListWidget, QListWidgetItem,
    QVBoxLayout
)
from PySide6.QtCore import Qt, QEvent

from .commands import CommandRegistry, fuzzy_score


class CommandPalette(QDialog):
    def __init__(self, registry: CommandRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите команду...")
        self.input.textChanged.connect(self.refresh)
        self.input.installEventFilter(self)
        layout.addWidget(self.input)

        self.list = QListWidget()
        self.list.itemActivated.connect(self.run_selected)
        self.list.itemClicked.connect(self.run_selected)
        layout.addWidget(self.list)

        self.setStyleSheet("""
            QDialog { background: #252526; border: 1px solid #454545; }
            QLineEdit {
                background: #3c3c3c; color: #d4d4d4;
                border: none; padding: 8px 12px;
                font-size: 14px;
            }
            QListWidget {
                background: #252526; color: #cccccc;
                border: none; outline: none;
                font-size: 13px;
            }
            QListWidget::item { padding: 6px 12px; }
            QListWidget::item:selected { background: #094771; }
        """)

        self.refresh("")

    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Down:
                self.list.setCurrentRow(min(self.list.currentRow() + 1,
                                            self.list.count() - 1))
                return True
            if key == Qt.Key_Up:
                self.list.setCurrentRow(max(self.list.currentRow() - 1, 0))
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self.run_selected()
                return True
            if key == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)

    def refresh(self, text: str):
        self.list.clear()
        scored = []
        for cmd in self.registry.all():
            s = fuzzy_score(text, cmd.search_text)
            if s >= 0:
                scored.append((s, cmd))
        scored.sort(key=lambda x: -x[0])

        for _, cmd in scored:
            label = cmd.full_title
            if cmd.shortcut:
                label += f"    ({cmd.shortcut})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, cmd.id)
            self.list.addItem(item)

        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    def run_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        cmd_id = item.data(Qt.UserRole)
        self.close()
        QApplication.processEvents()
        self.registry.execute(cmd_id)

    def show_centered(self):
        parent = self.parent()
        if parent:
            geo = parent.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() // 4
            self.move(x, y)
        self.show()
        self.input.setFocus()
        self.input.selectAll()