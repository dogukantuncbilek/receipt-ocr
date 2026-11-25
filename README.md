# receipt-ocr

[![ci](https://github.com/dogukantuncbilek/receipt-ocr/actions/workflows/ci.yml/badge.svg)](https://github.com/dogukantuncbilek/receipt-ocr/actions/workflows/ci.yml)

Photograph a receipt, get the text and the fields that matter (total, VAT, date, tax id, receipt number) back as JSON. Built for Turkish fuel and shop receipts, but the pipeline is language-agnostic apart from the field patterns.

The interesting part is not the OCR engine, it is what happens before it. Phone photos of thermal receipts are low-contrast, noisy and unevenly lit; Tesseract on the raw photo returns garbage. The preprocessing step turns the photo into something a 1990s scanner would have produced, and then several Tesseract page-segmentation strategies compete, ranked by the engine's own confidence.

```
photo -> upscale to 1000 px -> grayscale -> bilateral filter -> Gaussian blur -> CLAHE
      -> Otsu / adaptive-mean / adaptive-Gaussian thresholds (brightest wins) -> morphology
      -> Tesseract psm 6 / 4 / 3 / whitelist / tur-only (+ EasyOCR if installed)
      -> clean lines, normalise prices -> regex field extraction
```

## Run it

Docker, both services:

```bash
docker compose up --build
# UI on http://localhost:8080, API on http://localhost:8000
```

Locally (needs the `tesseract` binary with the `tur` language pack on PATH, or `TESSERACT_CMD` pointing at it):

```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload                     # http://localhost:8000/docs

cd ../frontend
npm install && npm run dev                         # http://localhost:5173, proxies /api to the backend
```

EasyOCR is optional (`pip install -e ".[easyocr]"`, pulls PyTorch); when importable it joins the engine list automatically.

## API

`POST /ocr` with a multipart `file` (JPG/PNG, up to 10 MB). Add `?debug=true` to get the preprocessed image back as a data URL.

```json
{
  "results": [
    {"engine": "tesseract-psm6", "text": "ORNEK AKARYAKIT A.S.\n...\nTOPLAM 1420,55", "confidence": 92.3},
    {"engine": "tesseract-psm4", "text": "...", "confidence": 90.1}
  ],
  "fields": {
    "total": "1420,55", "vat": "236,76", "cash": "1420,55",
    "receipt_no": "A0042", "pump_no": "3", "plate": "06ABC123",
    "tax_office": "KIZILAY", "tax_id": "1234567890",
    "date": "25.11.2026", "time": "14:32"
  },
  "engines_tried": 5
}
```

Results are sorted by confidence; the fields are extracted from the best one. If no engine produced at least 10 characters, `results` is empty and `fields` is `{}`.

`GET /health` reports whether the Tesseract binary was found.

## Layout

| Path | What |
|---|---|
| `backend/app/preprocess.py` | OpenCV pipeline, every step a small function with a `PreprocessOptions` dataclass for the knobs |
| `backend/app/engines.py` | Tesseract strategies, optional EasyOCR, confidence scoring, engine registry |
| `backend/app/postprocess.py` | line cleanup, price normalisation (`12.50` → `12,50`) |
| `backend/app/fields.py` | regex table for Turkish receipt fields, fallback total guess |
| `backend/app/main.py` | FastAPI: `/ocr`, `/health`, CORS from `CORS_ORIGINS` |
| `backend/tests/` | preprocessing invariants, field extraction, API with a fake engine, and one real-Tesseract test on a synthetic receipt |
| `frontend/` | Vue 3 + Vite uploader: engine selector, editable field table, optional preprocessed-image view |
| `scripts/make_sample.py` | renders the synthetic receipt used by the tests and `samples/` (no real receipts in the repo) |

## Tuning

- Thresholding picks the candidate with the most white pixels; on receipts that over-expose, swap `pick_threshold` for Otsu only.
- `PreprocessOptions.min_height` controls the upscale; 1000 px is the sweet spot for Tesseract's default 300 dpi assumption on a 7 cm wide receipt.
- Add a field: one `(key, regex)` tuple in `fields.py`, one assertion in `test_fields.py`.
- Add an engine: a callable `Image -> OcrResult | None` appended in `default_engines()`.

## License

MIT
