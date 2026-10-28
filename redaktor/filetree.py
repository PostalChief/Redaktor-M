import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog, QMenu, QInputDialog, QMessageBox
)
from PySide6.QtCore import QDir, QModelIndex, Qt
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
        
        # Включаем контекстное меню
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
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

    def apply_theme(self, t):
        pass # Заглушка для совместимости

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
        return self.model.filePath(self.tree.rootIndex())

    def _on_double_click(self, index: QModelIndex):
        path = self.model.filePath(index)
        if os.path.isfile(path) and self.on_file_double_clicked:
            self.on_file_double_clicked(path)

    # ============================================================
    #  КОНТЕКСТНОЕ МЕНЮ (Создание, удаление, переименование)
    # ============================================================
    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #2d2d30; color: #d4d4d4; border: 1px solid #3c3c3c; }
            QMenu::item:selected { background: #094771; }
        """)

        # Получаем путь к текущему выбранному элементу
        path = ""
        is_dir = False
        if index.isValid():
            path = self.model.filePath(index)
            is_dir = self.model.isDir(index)
        else:
            # Если кликнули по пустому месту — работаем с корневой папкой
            path = self.current_folder()
            is_dir = True

        # Опции, если выбран файл или папка
        if path and is_dir:
            action_new_file = menu.addAction("📄 Создать файл")
            action_new_file.triggered.connect(lambda: self._create_file(path))
            
            action_new_folder = menu.addAction("📁 Создать папку")
            action_new_folder.triggered.connect(lambda: self._create_folder(path))

        if index.isValid():
            menu.addSeparator()
            action_rename = menu.addAction("✏️ Переименовать")
            action_rename.triggered.connect(lambda: self._rename_item(path))
            
            action_delete = menu.addAction("❌ Удалить")
            action_delete.triggered.connect(lambda: self._delete_item(path))

        # Показываем меню
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def _create_file(self, folder_path):
        name, ok = QInputDialog.getText(self, "Создать файл", "Введите имя файла (с расширением):")
        if ok and name:
            full_path = os.path.join(folder_path, name)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    pass # Создаём пустой файл
                # Если есть callback для открытия — можно сразу открыть
                if self.on_file_double_clicked:
                    self.on_file_double_clicked(full_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл:\n{e}")

    def _create_folder(self, folder_path):
        name, ok = QInputDialog.getText(self, "Создать папку", "Введите имя папки:")
        if ok and name:
            full_path = os.path.join(folder_path, name)
            try:
                os.makedirs(full_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать папку:\n{e}")

    def _rename_item(self, old_path):
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать:\n{e}")

    def _delete_item(self, path):
        name = os.path.basename(path)
        msg = f"Вы уверены, что хотите удалить «{name}»?"
        res = QMessageBox.question(self, "Удаление", msg, QMessageBox.Yes | QMessageBox.No)
        
        if res == QMessageBox.Yes:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")