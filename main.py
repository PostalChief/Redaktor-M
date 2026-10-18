import sys
import os
from PySide6.QtWidgets import QApplication

from redaktor.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Redaktor-M")

    app.setStyleSheet("""
        QMainWindow, QMenuBar, QMenu, QStatusBar {
            background-color: #2d2d30;
            color: #d4d4d4;
        }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: #094771;
        }
        QStatusBar { background: #007acc; color: white; }
        QMenu {
            padding: 4px 0;
        }
        QMenu::item {
            padding: 6px 32px 6px 24px;
            min-width: 180px;
        }
    """)

    win = MainWindow()
    win.show()

    # Открытие файлов из командной строки (для контекстного меню Windows)
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            win.open_path(arg)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()