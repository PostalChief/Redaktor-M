import os
import json


RECENT_DIR = os.path.join(os.path.expanduser("~"), ".redaktor")
RECENT_FILE = os.path.join(RECENT_DIR, "recent.json")
MAX_RECENT = 10


def load_recent() -> list[str]:
    """Возвращает список последних файлов (только существующие)."""
    try:
        if not os.path.isfile(RECENT_FILE):
            return []
        with open(RECENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # Оставляем только существующие файлы
        return [p for p in data if isinstance(p, str) and os.path.isfile(p)]
    except Exception:
        return []


def save_recent(paths: list[str]):
    try:
        os.makedirs(RECENT_DIR, exist_ok=True)
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(paths[:MAX_RECENT], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[recent] Не удалось сохранить: {e}")


def add_recent(path: str) -> list[str]:
    """Добавляет файл наверх списка, убирает дубликаты, обрезает до MAX."""
    if not path:
        return load_recent()
    path = os.path.abspath(path)
    items = load_recent()
    # Убираем старую запись, если есть
    items = [p for p in items if os.path.abspath(p) != path]
    # Вставляем наверх
    items.insert(0, path)
    items = items[:MAX_RECENT]
    save_recent(items)
    return items


def clear_recent():
    try:
        if os.path.isfile(RECENT_FILE):
            os.remove(RECENT_FILE)
    except Exception:
        pass