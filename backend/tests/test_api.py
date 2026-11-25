import pytest
from fastapi.testclient import TestClient

from app import engines, main
from app.engines import OcrResult


@pytest.fixture
def client(monkeypatch):
    fake_text = "TOPLAM 42,00\nKDV 7,00\nTARIH: 01.02.2026"
    main.get_engines.cache_clear()
    monkeypatch.setattr(main, "get_engines", lambda: [lambda img: OcrResult("fake", fake_text, 88.0)])
    return TestClient(main.app)


def test_health_reports_tesseract_flag(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert isinstance(response.json()["tesseract"], bool)


def test_ocr_returns_results_and_fields(client, receipt_png):
    response = client.post("/ocr", files={"file": ("receipt.png", receipt_png, "image/png")})

    body = response.json()
    assert response.status_code == 200
    assert body["results"][0]["engine"] == "fake"
    assert body["fields"]["total"] == "42,00"
    assert body["fields"]["vat"] == "7,00"
    assert "processed_image" not in body


def test_debug_flag_returns_processed_image(client, receipt_png):
    response = client.post("/ocr?debug=true", files={"file": ("receipt.png", receipt_png, "image/png")})

    assert response.json()["processed_image"].startswith("data:image/png;base64,")


def test_non_image_upload_is_rejected(client):
    response = client.post("/ocr", files={"file": ("x.txt", b"hello", "text/plain")})

    assert response.status_code == 400


@pytest.mark.skipif(not engines.tesseract_available(), reason="tesseract binary not installed")
def test_real_tesseract_reads_the_synthetic_receipt(receipt_png):
    main.get_engines.cache_clear()
    response = TestClient(main.app).post("/ocr", files={"file": ("receipt.png", receipt_png, "image/png")})

    body = response.json()
    assert response.status_code == 200
    assert body["results"], "no engine produced text"
    texts = "\n".join(r["text"].upper() for r in body["results"])
    assert "TOPLAM" in texts
    assert "total" in body["fields"] or "total_guess" in body["fields"]
