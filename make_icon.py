"""
Генератор иконки для Redaktor.
Рисует стилизованную "M" на тёмном фоне с акцентом.
"""
from PIL import Image, ImageDraw, ImageFont
import os

# --- Настройки ---
BG_COLOR = (30, 30, 30)        # тёмный фон
ACCENT = (86, 156, 214)         # синий акцент (как ключевые слова в подсветке)
TEXT_COLOR = (212, 212, 212)    # светлый текст
LETTER = "R"

# Размеры, которые Windows ожидает в .ico
SIZES = [16, 24, 32, 48, 64, 128, 256, 512]


def draw_icon(size: int) -> Image.Image:
    """Рисует одну версию иконки заданного размера."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Скруглённый квадрат-фон
    radius = max(2, size // 6)
    d.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=BG_COLOR,
        outline=ACCENT,
        width=max(1, size // 32),
    )

    # Полоска-акцент сверху (имитирует "шапку" редактора)
    bar_h = max(2, size // 8)
    d.rounded_rectangle(
        [(0, 0), (size - 1, bar_h)],
        radius=radius,
        fill=ACCENT,
    )
    # Закрываем нижние углы полоски, чтобы она не была скруглённой снизу
    d.rectangle([(0, bar_h // 2), (size - 1, bar_h)], fill=ACCENT)

    # Буква "M" по центру
    # Подбираем размер шрифта под размер иконки
    font = None
    for candidate in ("arialbd.ttf", "arial.ttf", "segoeuib.ttf", "segoeui.ttf"):
        try:
            font = ImageFont.truetype(candidate, int(size * 0.55))
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = d.textbbox((0, 0), LETTER, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] + size // 12  # чуть ниже, чтобы не прилипала к полоске
    d.text((tx, ty), LETTER, font=font, fill=TEXT_COLOR)

    return img


def main():
    # Рисуем самую большую версию
    images = [draw_icon(s) for s in SIZES]
    # Сохраняем в .ico с несколькими размерами
    out = "app.ico"
    images[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=images[1:],
    )
    print(f"Готово: {os.path.abspath(out)}")

    # Заодно сохраним превью в PNG для удобства
    images[-1].save("app_preview.png")
    print(f"Превью: {os.path.abspath('app_preview.png')}")
    # Сохраним 512x512 отдельно
    draw_icon(512).save("app_512x512.png")
    print("Сохранено: app_512x512.png")


if __name__ == "__main__":
    main()