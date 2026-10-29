import re
from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import Qt, QStringListModel


class CodeCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchStartsWith) # Ищем только те слова, которые начинаются с введенного
        self.setModel(QStringListModel([]))
        
        # Настраиваем всплывающее окно
        popup = self.popup()
        popup.setStyleSheet("""
            QListView {
                background: #252526;
                color: #d4d4d4;
                border: 1px solid #454545;
                selection-background-color: #094771;
            }
        """)
        self.activated.connect(self._on_activated)

    def update_words(self, text: str):
        """Собирает все уникальные слова из текста и обновляет модель."""
        # Ищем слова, состоящие из букв, цифр и подчеркивания (длина 3+)
        words = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text))
        
        # Сортируем для удобства
        word_list = sorted(list(words), key=str.lower)
        
        # Обновляем модель
        model = self.model()
        if isinstance(model, QStringListModel):
            model.setStringList(word_list)

    def _on_activated(self, text):
        """Вызывается при выборе слова из списка."""
        widget = self.parent()
        if widget:
            cursor = widget.textCursor()
            cursor.insertText(text)
            widget.setTextCursor(cursor)