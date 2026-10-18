import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog
)
from PySide6.QtCore import QDir, QModelIndex
from PySide6.QtWidgets import QFileSystemModel


class FileTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.on_file_double_clicked = None
        self.on_folder_changed = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top = QWidget()
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(6, 6, 6, 6)
        self.btn_open = QPushButton("📂 Открыть папку")
        self.btn_open.clicked.connect(self.choose_folder)
        top_layout.addWidget(self.btn_open)
        layout.addWidget(top)

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(False)
        self.tree.setIndentation(14)
        self.tree.setSortingEnabled(False)
        self.tree.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree)

        self.tree.setStyleSheet("""
            QTreeView {
                background: #252526; color: #cccccc;
                border: none; outline: none;
            }
            QTreeView::item:selected { background: #094771; }
            QTreeView::item:hover    { background: #2a2d2e; }
            QPushButton {
                background: #3c3c3c; color: #cccccc;
                border: 1px solid #555;
                padding: 4px 8px; border-radius: 3px;
            }
            QPushButton:hover { background: #4a4a4a; }
        """)

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Открыть папку")
        if path:
            self.open_folder(path)

    def open_folder(self, path):
        self.tree.setRootIndex(self.model.index(path))
        self.tree.expand(self.model.index(path))
        if self.on_folder_changed:
            self.on_folder_changed(path)

    def current_folder(self):
        """Возвращает путь текущей корневой папки проекта."""
        return self.model.filePath(self.tree.rootIndex())

    def _on_double_click(self, index: QModelIndex):
        path = self.model.filePath(index)
        if os.path.isfile(path) and self.on_file_double_clicked:
            self.on_file_double_clicked(path)