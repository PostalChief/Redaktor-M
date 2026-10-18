import os
from PySide6.QtWidgets import (
    QApplication, QDialog, QLineEdit, QListWidget, QListWidgetItem,
    QVBoxLayout
)
from PySide6.QtCore import Qt, QEvent

from .commands import fuzzy_score


# Папки, которые не сканируем — экономим время и не засоряем список
IGNORED_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", "env", ".env",
    ".idea", ".vscode",
    "dist", "build", ".tox",
    ".next", ".nuxt", "target",
    "site-packages",
}

# Расширения-мусор, которые не хотим показывать
IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd",
    ".exe", ".dll", ".so", ".dylib",
    ".o", ".obj", ".class",
    ".log", ".tmp", ".cache",
    ".lock",
}

# Максимум файлов, которые сканируем — защита от гигантских репо
MAX_FILES = 20000


class FileFinder(QDialog):
    """
    Всплывающее окно fuzzy-поиска файлов проекта.
    Похоже на CommandPalette, но ищет по путям файлов.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setModal(True)
        self.resize(700, 450)

        self._root: str = ""              # корневая папка проекта
        self._all_files: list[str] = []   # полные пути всех файлов
        self._on_open = None              # callback(path) при выборе

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Введите имя файла...")
        self.input.textChanged.connect(self.refresh)
        self.input.installEventFilter(self)
        layout.addWidget(self.input)

        self.list = QListWidget()
        self.list.itemActivated.connect(self.open_selected)
        self.list.itemClicked.connect(self.open_selected)
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

    # ---------- настройка ----------
    def set_root(self, path: str):
        """Устанавливает корневую папку проекта и пересканирует файлы."""
        if not path or not os.path.isdir(path):
            self._root = ""
            self._all_files = []
            return
        self._root = path
        self._scan_files()

    def set_on_open(self, callback):
        """callback(path) — что делать при выборе файла."""
        self._on_open = callback

    # ---------- сканирование ----------
    def _scan_files(self):
        """Рекурсивно собирает все файлы проекта, пропуская мусор."""
        result = []
        for dirpath, dirnames, filenames in os.walk(self._root):
            # Фильтруем подпапки на месте (os.walk учитывает in-place)
            dirnames[:] = [
                d for d in dirnames
                if d not in IGNORED_DIRS and not d.startswith(".")
            ]
            # Скрытые папки пропускаем полностью, но только верхнего уровня
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in IGNORED_EXTENSIONS:
                    continue
                full = os.path.join(dirpath, fname)
                result.append(full)
                if len(result) >= MAX_FILES:
                    break
            if len(result) >= MAX_FILES:
                break
        self._all_files = result

    # ---------- показ ----------
    def show_centered(self):
        if not self._all_files:
            return  # нечего показывать
        self.input.clear()
        self.refresh("")
        parent = self.parent()
        if parent:
            geo = parent.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + geo.height() // 5
            self.move(x, y)
        self.show()
        self.input.setFocus()

    # ---------- фильтрация ----------
    def refresh(self, text: str):
        self.list.clear()
        if not self._root:
            return

        scored = []
        for full_path in self._all_files:
            rel = os.path.relpath(full_path, self._root)
            # Ищем по относительному пути + по имени файла
            s = max(
                fuzzy_score(text, rel),
                fuzzy_score(text, os.path.basename(full_path)),
            ) if text else 0
            if text and s < 0:
                continue
            # Бонус за короткие пути (обычно важные файлы — ближе к корню)
            if not text:
                s = -len(rel)
            scored.append((s, full_path, rel))

        # Сортировка: по счёту, потом по длине пути
        scored.sort(key=lambda x: (-x[0], len(x[2])))

        for _, full_path, rel in scored[:200]:  # ограничим вывод
            item = QListWidgetItem(rel.replace("\\", "/"))
            item.setData(Qt.UserRole, full_path)
            self.list.addItem(item)

        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    # ---------- обработка клавиш ----------
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
                self.open_selected()
                return True
            if key == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, event)

    def open_selected(self):
        item = self.list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        self.close()
        QApplication.processEvents()
        if self._on_open:
            self._on_open(path)