import os
import shutil
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pytesseract
from PIL import Image

from .postprocess import clean_text

MIN_CHARS = 10
WHITELIST = "0123456789ABCÇDEFGĞHIİJKLMNOÖPQRSŞTUÜVWXYZabcçdefgğhıijklmnoöpqrsştuüvwxyz.:,/-()+*%₺ "


@dataclass(frozen=True)
class OcrResult:
    engine: str
    text: str
    confidence: float

    def as_dict(self) -> dict:
        return {"engine": self.engine, "text": self.text, "confidence": round(self.confidence, 1)}


@dataclass(frozen=True)
class TesseractStrategy:
    name: str
    config: str
    lang: str = "tur+eng"


STRATEGIES: tuple[TesseractStrategy, ...] = (
    TesseractStrategy("tesseract-psm6", "--psm 6 --oem 3"),
    TesseractStrategy("tesseract-psm4", "--psm 4 --oem 3"),
    TesseractStrategy("tesseract-psm3", "--psm 3 --oem 3"),
    TesseractStrategy("tesseract-psm6-whitelist", f"--psm 6 --oem 3 -c tessedit_char_whitelist={WHITELIST}"),
    TesseractStrategy("tesseract-psm6-tur", "--psm 6 --oem 3", lang="tur"),
)

Engine = Callable[[Image.Image], OcrResult | None]


def configure_tesseract() -> None:
    explicit = os.environ.get("TESSERACT_CMD")
    if explicit:
        pytesseract.pytesseract.tesseract_cmd = explicit
        return
    if os.name == "nt" and shutil.which("tesseract") is None:
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default):
            pytesseract.pytesseract.tesseract_cmd = default


def tesseract_available() -> bool:
    configure_tesseract()
    try:
        pytesseract.get_tesseract_version()
        return True
    except pytesseract.TesseractNotFoundError:
        return False


def tesseract_confidence(image: Image.Image, strategy: TesseractStrategy) -> float:
    data = pytesseract.image_to_data(image, lang=strategy.lang, config=strategy.config, output_type=pytesseract.Output.DICT)
    scores = [float(c) for c in data["conf"] if float(c) > 0]
    return sum(scores) / len(scores) if scores else 0.0


def run_tesseract(image: Image.Image, strategy: TesseractStrategy) -> OcrResult | None:
    text = clean_text(pytesseract.image_to_string(image, lang=strategy.lang, config=strategy.config))
    if len(text) < MIN_CHARS:
        return None
    return OcrResult(strategy.name, text, tesseract_confidence(image, strategy))


def tesseract_engines() -> list[Engine]:
    return [lambda img, s=s: run_tesseract(img, s) for s in STRATEGIES]


def easyocr_engine() -> Engine | None:
    try:
        import easyocr
    except ImportError:
        return None

    reader = easyocr.Reader(["tr", "en"], gpu=False)

    def run(image: Image.Image) -> OcrResult | None:
        hits = reader.readtext(np.array(image))
        if not hits:
            return None
        text = clean_text("\n".join(t for _, t, _ in hits))
        if len(text) < MIN_CHARS:
            return None
        return OcrResult("easyocr", text, 100 * sum(c for _, _, c in hits) / len(hits))

    return run


def default_engines() -> list[Engine]:
    engines = tesseract_engines()
    easy = easyocr_engine()
    if easy is not None:
        engines.append(easy)
    return engines


def run_all(image: Image.Image, engines: list[Engine]) -> list[OcrResult]:
    results: list[OcrResult] = []
    for engine in engines:
        try:
            result = engine(image)
        except pytesseract.TesseractError:
            continue
        if result is not None:
            results.append(result)
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results
