import os
import json


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".redaktor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "language": "ru",
    "font_size": 11,
    "theme": "dark",
    "autosave": False,
    "utf8_bom": False,
}


def load_config() -> dict:
    try:
        if not os.path.isfile(CONFIG_FILE):
            return dict(DEFAULTS)
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Мержим с дефолтами
        result = dict(DEFAULTS)
        result.update(data)
        return result
    except Exception:
        return dict(DEFAULTS)


def save_config(data: dict):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[config] Не удалось сохранить конфиг: {e}")