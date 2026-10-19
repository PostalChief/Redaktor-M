from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
import re

class PygmentsHighlighter(QSyntaxHighlighter):
    def __init__(self, document, language: str = "text"):
        super().__init__(document)
        self.rules = []
        self.language = language
        
        try:
            # Получаем лексер для выбранного языка
            self.lexer = get_lexer_by_name(language)
        except Exception:
            # Если язык неизвестен — просто ничего не подсвечиваем
            self.lexer = None
            return

        # Маппинг базовых токенов Pygments на цвета (наша тёмная тема)
        self.token_colors = {
            Token.Keyword: QColor("#569cd6"),       # def, if, return
            Token.Name.Builtin: QColor("#4ec9b0"),  # print, len
            Token.Name.Function: QColor("#dcdcaa"), # имена функций
            Token.Name.Class: QColor("#4ec9b0"),    # имена классов
            Token.Name.Tag: QColor("#569cd6"),      # HTML/XML теги
            Token.Name.Attribute: QColor("#9cdcfe"),
            Token.Literal.String: QColor("#ce9178"), # строки
            Token.Literal.Number: QColor("#b5cea8"), # числа
            Token.Comment: QColor("#6a9955"),       # комментарии
            Token.Operator: QColor("#d4d4d4"),
            Token.Punctuation: QColor("#d4d4d4"),
        }

        # Разбиваем текст на слова и применяем регулярки
        # Pygments не даёт готовых регулярок, поэтому мы будем 
        # токенизировать документ целиком при изменении
        # (Для очень больших файлов это может быть медленно, 
        # но для файлов до 5000 строк — отлично)

    def highlightBlock(self, text):
        if not self.lexer:
            return

        # Хак: мы не можем прогнать весь документ через highlightBlock,
        # так как он вызывается построчно. Поэтому токенизируем только текущую строку.
        # (В будущем можно кэшировать результат для всего документа)
        
        # Получаем токены для этой строки
        tokens = list(self.lexer.get_tokens(text))
        
        # Проходим по токенам и красим
        position = 0
        for token_type, value in tokens:
            # Ищем цвет для токена (ищем самый специфичный)
            color = None
            for t_type, t_color in self.token_colors.items():
                if token_type in t_type:
                    color = t_color
                    break
            
            if color:
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                
                # Для ключевых слов и классов — жирный
                if token_type in Token.Keyword or token_type in Token.Name.Class:
                    fmt.setFontWeight(QFont.Bold)
                
                self.setFormat(position, len(value), fmt)
            
            position += len(value)