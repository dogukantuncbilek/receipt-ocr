import base64
import io
import os
from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from . import engines as ocr_engines
from .fields import extract_fields
from .preprocess import preprocess, to_pil

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(title="receipt-ocr", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_engines() -> list[ocr_engines.Engine]:
    ocr_engines.configure_tesseract()
    return ocr_engines.default_engines()


def encode_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "tesseract": ocr_engines.tesseract_available()}


@app.post("/ocr")
async def ocr(file: UploadFile = File(...), debug: bool = False) -> dict:
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image larger than 10 MB")
    try:
        original = Image.open(io.BytesIO(contents))
        original.load()
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="File is not an image") from exc

    processed = to_pil(preprocess(original))
    results = ocr_engines.run_all(processed, get_engines())
    best = results[0].text if results else ""
    response = {
        "results": [r.as_dict() for r in results],
        "fields": extract_fields(best),
        "engines_tried": len(get_engines()),
    }
    if debug:
        response["processed_image"] = encode_png(processed)
    return response
