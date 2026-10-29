import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor

from .i18n import tr

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", 
    ".mypy_cache", ".ruff_cache", "node_modules", ".venv", 
    "venv", "env", ".env", ".idea", ".vscode", "dist", "build", 
    ".next", ".nuxt", "target", "site-packages"
}

IGNORED_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".iso",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pyc", ".pyo", ".class", ".o", ".obj", ".lock"
}

class SearchThread(QThread):
    """Фоновый поток для поиска, чтобы не вешать интерфейс."""
    result_found = Signal(str, int, str) # filepath, line_num, text
    finished = Signal(int)               # count

    def __init__(self, root, query):
        super().__init__()
        self.root = root
        self.query = query

    def run(self):
        count = 0
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in IGNORED_EXTENSIONS:
                    continue
                
                filepath = os.path.join(dirpath, filename)
                try:
                    if os.path.getsize(filepath) > 1024 * 1024:
                        continue
                except OSError:
                    continue

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except (UnicodeDecodeError, PermissionError, OSError):
                    continue

                for line_num, line in enumerate(lines, 1):
                    if self.query in line:
                        text = line.strip()
                        if len(text) > 80:
                            text = text[:77] + "..."
                        self.result_found.emit(filepath, line_num, text)
                        count += 1
        
        self.finished.emit(count)


class ProjectSearchPanel(QWidget):
    file_opened = Signal(str, int)

    def __init__(self, get_root_folder, parent=None):
        super().__init__(parent)
        self.get_root_folder = get_root_folder
        self.thread = None
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        row1 = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(tr("projectsearch.placeholder"))
        self.input_search.returnPressed.connect(self.start_search)
        row1.addWidget(self.input_search, 1)

        self.btn_search = QPushButton(tr("projectsearch.button"))
        self.btn_search.clicked.connect(self.start_search)
        row1.addWidget(self.btn_search)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedWidth(32)
        self.btn_close.clicked.connect(self.hide)
        row1.addWidget(self.btn_close)

        layout.addLayout(row1)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #858585;")
        layout.addWidget(self.lbl_status)

        self.list_results = QListWidget()
        self.list_results.itemClicked.connect(self._on_result_clicked)
        layout.addWidget(self.list_results)

        self.setStyleSheet("""
            ProjectSearchPanel {
                background: #252526;
                border-top: 1px solid #3c3c3c;
            }
            QLineEdit {
                background: #3c3c3c; color: #d4d4d4;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton {
                background: #3c3c3c; color: #d4d4d4;
                border: 1px solid #555; border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:disabled { background: #2a2a2a; color: #666; }
            QListWidget {
                background: #1e1e1e; color: #d4d4d4;
                border: none;
            }
            QListWidget::item { padding: 4px; }
            QListWidget::item:selected { background: #094771; }
        """)

    def show_panel(self):
        self.show()
        self.input_search.setFocus()
        self.input_search.selectAll()

    def start_search(self):
        query = self.input_search.text()
        if not query:
            return

        # Если поток уже работает, не запускаем новый
        if self.thread and self.thread.isRunning():
            return

        self.list_results.clear()
        self.lbl_status.setText(tr("projectsearch.searching"))
        self.btn_search.setEnabled(False)
        self.input_search.setEnabled(False)

        root = self.get_root_folder()
        if not root or not os.path.isdir(root):
            self.lbl_status.setText(tr("projectsearch.no_folder"))
            self.btn_search.setEnabled(True)
            self.input_search.setEnabled(True)
            return

        # Запускаем фоновый поток
        self.thread = SearchThread(root, query)
        self.thread.result_found.connect(self._add_result)
        self.thread.finished.connect(self._search_finished)
        self.thread.start()

    def _add_result(self, filepath, line_num, text):
        from PySide6.QtCore import QFileInfo
        # Получаем относительный путь для красоты
        root = self.get_root_folder()
        try:
            rel_path = os.path.relpath(filepath, root)
        except ValueError:
            rel_path = filepath
            
        display_text = f"{rel_path}:{line_num}: {text}"
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, (filepath, line_num))
        item.setForeground(QColor("#d4d4d4"))
        self.list_results.addItem(item)

    def _search_finished(self, count):
        self.btn_search.setEnabled(True)
        self.input_search.setEnabled(True)
        if count == 0:
            self.lbl_status.setText(tr("projectsearch.not_found"))
        else:
            self.lbl_status.setText(tr("projectsearch.found", count=count))

    def _on_result_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            filepath, line_num = data
            self.file_opened.emit(filepath, line_num)