from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
import enchant
import re


class SpellChecker(QSyntaxHighlighter):
    def __init__(self, document, language="ru_RU"):
        super().__init__(document)
        
        # Загружаем словарь
        try:
            self.dictionary = enchant.Dict(language)
        except Exception as e:
            print(f"[spell] ОШИБКА загрузки словаря: {e}")
            self.dictionary = None

        # Используем стандартный Python-модуль re (он отлично понимает кириллицу)
        self.word_re = re.compile(r"[а-яА-ЯёЁa-zA-Z]+")

        # Формат для ошибок (классическое красное волнистое подчёркивание)
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        self.error_format.setUnderlineColor(QColor("#f48771"))

    def highlightBlock(self, text):
        if not self.dictionary:
            return

        # Ищем все слова в строке
        for match in self.word_re.finditer(text):
            word = match.group(0)
            
            # Проверяем слово
            if not self.dictionary.check(word):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, self.error_format)