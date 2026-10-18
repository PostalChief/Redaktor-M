import os
import json


SESSION_DIR = os.path.join(os.path.expanduser("~"), ".redaktor")
SESSION_FILE = os.path.join(SESSION_DIR, "session.json")


def save_session(data: dict):
    """Сохраняет словарь в ~/.redaktor/session.json."""
    try:
        os.makedirs(SESSION_DIR, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Не падаем, если не удалось сохранить — не критично
        print(f"[session] Не удалось сохранить сессию: {e}")


def load_session() -> dict:
    """Загружает сессию. При любой проблеме возвращает пустой словарь."""
    try:
        if not os.path.isfile(SESSION_FILE):
            return {}
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[session] Не удалось загрузить сессию: {e}")
        return {}


def clear_session():
    """Удаляет файл сессии (на случай отладки)."""
    try:
        if os.path.isfile(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass