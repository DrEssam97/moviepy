"""Check what moviepy's TextClip does with Arabic, with and without Raqm.

Renders the same Arabic line four ways and compares each with khatt's
rendering (HarfBuzz shaping + bidi, the reference):

* moviepy_plain   - moviepy.TextClip(text)
* moviepy_recipe  - moviepy.TextClip(get_display(reshape(text)))
* khatt_plain     - khatt.video.TextClip(text)                (reference)
* hb_recipe       - khatt.video.TextClip(get_display(reshape(text))):
                    the recipe through HarfBuzz + bidi, i.e. what Raqm does

Usage: python check_textclip.py OUT_DIR
"""

import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path

import arabic_reshaper
import numpy as np
from PIL import Image, ImageDraw, features

try:
    from bidi import get_display
except ImportError:
    from bidi.algorithm import get_display

from khatt.fonts import font_path
from khatt.video import TextClip as KhattTextClip
from moviepy import TextClip

TEXT = "مرحبا بالعالم"
FONT = str(font_path("amiri"))
ARGS = dict(font=FONT, font_size=72, color="black", bg_color="white", margin=(24, 24), transparent=False)


def ink(clip):
    return clip.get_frame(0).mean(axis=2) < 128


def crop(mask):
    rows, cols = np.where(mask)
    return mask[rows.min() : rows.max() + 1, cols.min() : cols.max() + 1]


def ink_runs(mask):
    cols = mask.any(axis=0).astype(int)
    return int(np.count_nonzero(np.diff(np.concatenate([[0], cols])) == 1))


def similarity(mask, reference):
    """IoU of the two ink masks, cropped and scaled to the same box."""
    a, b = crop(mask), crop(reference)
    a = np.array(Image.fromarray(a).resize(b.shape[::-1], Image.NEAREST))
    return round(float((a & b).sum() / (a | b).sum()), 3)


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    recipe = get_display(arabic_reshaper.reshape(TEXT))
    clips = {
        "moviepy_plain": TextClip(text=TEXT, **ARGS),
        "moviepy_recipe": TextClip(text=recipe, **ARGS),
        "khatt_plain": KhattTextClip(text=TEXT, **ARGS),
        "hb_recipe": KhattTextClip(text=recipe, **ARGS),
    }
    masks = {name: ink(clip) for name, clip in clips.items()}
    reference = masks["khatt_plain"]
    report = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "pillow": version("pillow"),
        "moviepy": version("moviepy"),
        "khatt": version("khatt"),
        "raqm": features.check("raqm"),
        "cases": {
            name: {"ink_runs": ink_runs(mask), "iou_vs_khatt": similarity(mask, reference)}
            for name, mask in masks.items()
        },
    }

    frames = [Image.fromarray(clips[name].get_frame(0)) for name in clips]
    width = max(f.width for f in frames) + 260
    sheet = Image.new("RGB", (width, sum(f.height for f in frames)), "white")
    draw = ImageDraw.Draw(sheet)
    y = 0
    for name, frame in zip(clips, frames):
        sheet.paste(frame, (260, y))
        case = report["cases"][name]
        draw.text((8, y + 20), f"{name}\nruns={case['ink_runs']}\niou={case['iou_vs_khatt']}", fill="black", font_size=22)
        draw.line([(0, y), (width, y)], fill="gray")
        y += frame.height
    sheet.save(out / f"textclip_raqm_{str(report['raqm']).lower()}.png")
    (out / f"report_raqm_{str(report['raqm']).lower()}.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
