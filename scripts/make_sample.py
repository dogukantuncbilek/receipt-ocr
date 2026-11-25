import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LINES = [
    ("ORNEK AKARYAKIT A.S.", True),
    ("ATATURK BLV. NO:1 ANKARA", False),
    ("VERGI DAIRESI: KIZILAY", False),
    ("VKN/TCKN: 1234567890", False),
    ("TARIH: 25.11.2026  SAAT: 14:32", False),
    ("FIS NO: A0042   Z NO: 118", False),
    ("POMPA NO: 3", False),
    ("PLAKA: 06ABC123", False),
    ("", False),
    ("KURSUNSUZ 95", False),
    ("35,40 LT x 40,12", False),
    ("KDV %20            236,76", False),
    ("TOPLAM            1420,55", True),
    ("NAKIT             1420,55", False),
    ("", False),
    ("TESEKKUR EDERIZ", False),
]

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def load_font(size: int) -> ImageFont.ImageFont:
    override = os.environ.get("SAMPLE_FONT")
    for path in ([override] if override else []) + FONT_CANDIDATES:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def render_receipt(width: int = 480, line_height: int = 34) -> Image.Image:
    font = load_font(22)
    bold = load_font(26)
    height = line_height * (len(LINES) + 2)
    image = Image.new("RGB", (width, height), (247, 244, 236))
    draw = ImageDraw.Draw(image)
    y = line_height // 2
    for text, strong in LINES:
        draw.text((24, y), text, fill=(30, 30, 30), font=bold if strong else font)
        y += line_height
    return image


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path("samples/receipt-sample.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    render_receipt().save(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
