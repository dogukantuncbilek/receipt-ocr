import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from make_sample import render_receipt  # noqa: E402


@pytest.fixture(scope="session")
def receipt_image() -> Image.Image:
    return render_receipt()


@pytest.fixture(scope="session")
def receipt_png(receipt_image: Image.Image) -> bytes:
    import io

    buffer = io.BytesIO()
    receipt_image.save(buffer, format="PNG")
    return buffer.getvalue()
