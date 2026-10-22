"""Comparison grid for the PR: the same clips without Raqm (Windows) and with Raqm (Linux)."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

win, linux, out = (Path(p) for p in sys.argv[1:4])

GREEN, RED, GREY, INK = (22, 128, 61), (190, 30, 45), (110, 110, 110), (25, 25, 25)
UI = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
UI_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)

ROWS = [
    ("moviepy_plain", 'TextClip("مرحبا بالعالم")', ("letters apart, order reversed", RED), ("correct", GREEN)),
    ("moviepy_recipe", "TextClip(get_display(reshape(...)))", ("readable (simplified letter forms)", GREEN), ("order reversed", RED)),
    ("khatt_plain", 'khatt.video.TextClip("مرحبا بالعالم")', ("correct", GREEN), ("correct", GREEN)),
    ("hebrew_moviepy", 'TextClip("שלום עולם")', ("order reversed", RED), ("correct", GREEN)),
]
CELL_W, CELL_H, LABEL_W, HEAD_H, PAD = 470, 150, 430, 70, 16


def cell(path: Path) -> Image.Image:
    frame = Image.open(path).convert("RGB")
    frame.thumbnail((CELL_W - 2 * PAD, CELL_H - 50))
    return frame


sheet = Image.new("RGB", (LABEL_W + 2 * CELL_W, HEAD_H + len(ROWS) * CELL_H), "white")
draw = ImageDraw.Draw(sheet)
for col, title in enumerate(["Pillow without Raqm (Windows)", "Pillow with Raqm (Linux)"]):
    draw.text((LABEL_W + col * CELL_W + PAD, 22), title, font=UI_BOLD, fill=INK)
for row, (name, label, *verdicts) in enumerate(ROWS):
    top = HEAD_H + row * CELL_H
    draw.line([(0, top), (sheet.width, top)], fill=(220, 220, 220), width=2)
    code = label.replace("مرحبا بالعالم", "<Arabic>").replace("שלום עולם", "<Hebrew>")
    draw.text((PAD, top + CELL_H // 2 - 12), code, font=CODE, fill=INK)
    for col, (folder, tag) in enumerate([(win, "noraqm"), (linux, "raqm")]):
        frame = cell(folder / f"{tag}_{name}.png")
        left = LABEL_W + col * CELL_W
        sheet.paste(frame, (left + (CELL_W - frame.width) // 2, top + 8))
        text, colour = verdicts[col]
        width = draw.textlength(text, font=UI)
        draw.text((left + (CELL_W - width) / 2, top + CELL_H - 38), text, font=UI, fill=colour)
draw.line([(LABEL_W, HEAD_H), (LABEL_W, sheet.height)], fill=(220, 220, 220), width=2)
draw.line([(LABEL_W + CELL_W, 0), (LABEL_W + CELL_W, sheet.height)], fill=(220, 220, 220), width=2)
draw.text((PAD, 22), "Pillow 13.0, moviepy master", font=UI, fill=GREY)
sheet.save(out)
print(out, sheet.size)
