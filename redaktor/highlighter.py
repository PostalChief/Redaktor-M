from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtCore import QRegularExpression


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#569cd6"))
        kw_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "and","as","assert","async","await","break","class","continue",
            "def","del","elif","else","except","False","finally","for","from",
            "global","if","import","in","is","lambda","None","nonlocal","not",
            "or","pass","raise","return","True","try","while","with","yield",
            "self","print"
        ]
        for w in keywords:
            self.rules.append((QRegularExpression(rf"\b{w}\b"), kw_fmt))

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#ce9178"))
        self.rules.append((QRegularExpression(r'".*?"'), str_fmt))
        self.rules.append((QRegularExpression(r"'.*?'"), str_fmt))

        com_fmt = QTextCharFormat()
        com_fmt.setForeground(QColor("#6a9955"))
        self.rules.append((QRegularExpression(r"#[^\n]*"), com_fmt))

        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#b5cea8"))
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), num_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)