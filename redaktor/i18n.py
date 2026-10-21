"""
Простая система переводов.
Использование:
    from .i18n import tr, set_language, get_language
    print(tr("file.save"))  # "Сохранить" или "Save" в зависимости от языка
"""

LANGUAGES = {
    "ru": "Русский",
    "en": "English",
}

TRANSLATIONS = {
    "ru": {
        # --- Категории меню ---
        "menu.File": "Файл",
        "menu.Edit": "Редактирование",
        "menu.View": "Вид",
        "menu.Help": "Справка",
        "help.about": "О программе",
        "about.title": "О программе Redaktor-M",
        "about.text": "<h3>Redaktor-M</h3><p>Версия: {version}</p><p>Легкий текстовый редактор для Windows.</p><p>Сделано на Python и PySide6.</p>",

        # --- File ---
        "file.new": "Новый файл",
        "file.open": "Открыть файл...",
        "file.open_folder": "Открыть папку...",
        "file.save": "Сохранить",
        "file.save_as": "Сохранить как...",
        "file.close_tab": "Закрыть вкладку",
        "file.exit": "Выход",
        "file.autosave": "Автосохранение",
        "file.open_recent": "Открыть недавние",
        "file.clear_recent": "Очистить список недавних",
        "file.no_recent": "(пусто)",
        "file.utf8_bom": "Сохранять в UTF-8 с BOM",

        # --- Edit ---
        "edit.undo": "Отменить",
        "edit.redo": "Повторить",
        "edit.cut": "Вырезать",
        "edit.copy": "Копировать",
        "edit.paste": "Вставить",
        "edit.select_all": "Выделить всё",
        "edit.goto_line": "Перейти к строке...",
        "edit.find": "Найти...",
        "edit.replace": "Найти и заменить...",
        "edit.find_next": "Найти далее",
        "edit.find_prev": "Найти назад",
        "edit.select_next": "Выделить следующее вхождение",
        "edit.insert_date": "Вставить дату и время",

        # --- View ---
        "view.toggle_sidebar": "Показать/скрыть сайдбар",
        "view.font": "Шрифт...",
        "view.zoom_in": "Увеличить шрифт",
        "view.zoom_out": "Уменьшить шрифт",
        "view.zoom_reset": "Сбросить масштаб",
        "view.language": "Язык",
        "view.language.ru": "Русский",
        "view.language.en": "English",

        # --- Палитра и finder ---
        "palette.show": "Палитра команд",
        "file.goto_file": "Перейти к файлу...",

        # --- UI-элементы ---
        "ui.open_folder": "📂 Открыть папку",
        "ui.search_placeholder": "Найти",
        "ui.replace_placeholder": "Заменить на",
        "ui.palette_placeholder": "Введите команду...",
        "ui.finder_placeholder": "Введите имя файла...",
        "ui.replace_one": "Заменить",
        "ui.replace_all": "Заменить всё",
        "ui.no_matches": "Нет совпадений",
        "ui.matches": "{n} совпад.",
        "ui.match_of": "{i} из {n}",
        "ui.untitled": "Без имени",
        "ui.unsaved_title": "Не сохранено",
        "ui.unsaved_message": "Сохранить изменения в «{name}»?",
        "ui.error": "Ошибка",
        "ui.cant_read": "Не могу прочитать файл:\n{e}",
        "ui.goto_line_title": "Перейти к строке",
        "ui.goto_line_prompt": "Номер строки (1–{total}):",
        "ui.status_position": "Строка {line}, Колонка {col}",
        "ui.app_name": "Redaktor-M",
        "ui.autosave_on": "Автосохранение: вкл",
        "ui.autosave_off": "Автосохранение: выкл",
        "ui.saved": "✓ Сохранено",
        "ui.bom_on": "UTF-8 с BOM: вкл",
        "ui.bom_off": "UTF-8 с BOM: выкл",
    },
    "en": {
        # --- Menu categories ---
        "menu.File": "File",
        "menu.Edit": "Edit",
        "menu.View": "View",
        "menu.Help": "Help",
        "help.about": "About",
        "about.title": "About Redaktor-M",
        "about.text": "<h3>Redaktor-M</h3><p>Version: {version}</p><p>Lightweight text editor for Windows.</p><p>Built with Python and PySide6.</p>",

        # --- File ---
        "file.new": "New File",
        "file.open": "Open File...",
        "file.open_folder": "Open Folder...",
        "file.save": "Save",
        "file.save_as": "Save As...",
        "file.close_tab": "Close Tab",
        "file.exit": "Exit",
        "file.autosave": "Autosave",
        "file.open_recent": "Open Recent",
        "file.clear_recent": "Clear Recent",
        "file.no_recent": "(empty)",
        "file.utf8_bom": "Save as UTF-8 with BOM",

        # --- Edit ---
        "edit.undo": "Undo",
        "edit.redo": "Redo",
        "edit.cut": "Cut",
        "edit.copy": "Copy",
        "edit.paste": "Paste",
        "edit.select_all": "Select All",
        "edit.goto_line": "Go to Line...",
        "edit.find": "Find...",
        "edit.replace": "Find and Replace...",
        "edit.find_next": "Find Next",
        "edit.find_prev": "Find Previous",
        "edit.select_next": "Select Next Occurrence",
        "edit.insert_date": "Insert Date and Time",

        # --- View ---
        "view.toggle_sidebar": "Toggle Sidebar",
        "view.font": "Font...",
        "view.zoom_in": "Zoom In",
        "view.zoom_out": "Zoom Out",
        "view.zoom_reset": "Reset Zoom",
        "view.language": "Language",
        "view.language.ru": "Русский",
        "view.language.en": "English",

        # --- Palette and finder ---
        "palette.show": "Command Palette",
        "file.goto_file": "Go to File...",

        # --- UI elements ---
        "ui.open_folder": "📂 Open Folder",
        "ui.search_placeholder": "Find",
        "ui.replace_placeholder": "Replace with",
        "ui.palette_placeholder": "Type a command...",
        "ui.finder_placeholder": "Type a file name...",
        "ui.replace_one": "Replace",
        "ui.replace_all": "Replace All",
        "ui.no_matches": "No matches",
        "ui.matches": "{n} matches",
        "ui.match_of": "{i} of {n}",
        "ui.untitled": "Untitled",
        "ui.unsaved_title": "Unsaved changes",
        "ui.unsaved_message": "Save changes to \"{name}\"?",
        "ui.error": "Error",
        "ui.cant_read": "Cannot read file:\n{e}",
        "ui.goto_line_title": "Go to Line",
        "ui.goto_line_prompt": "Line number (1–{total}):",
        "ui.status_position": "Line {line}, Col {col}",
        "ui.app_name": "Redaktor-M",
        "ui.autosave_on": "Autosave: on",
        "ui.autosave_off": "Autosave: off",
        "ui.saved": "✓ Saved",
        "ui.bom_on": "UTF-8 with BOM: on",
        "ui.bom_off": "UTF-8 with BOM: off",
    },
}

_current_lang = "ru"


def set_language(lang: str):
    global _current_lang
    if lang in TRANSLATIONS:
        _current_lang = lang


def get_language() -> str:
    return _current_lang


def tr(key: str, **kwargs) -> str:
    """Возвращает перевод по ключу. Поддерживает {placeholders}."""
    translations = TRANSLATIONS.get(_current_lang, TRANSLATIONS["ru"])
    text = translations.get(key)
    if text is None:
        # Фолбэк на русский, если ключа нет в текущем языке
        text = TRANSLATIONS["ru"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text