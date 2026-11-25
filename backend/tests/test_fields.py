from app.fields import extract_fields
from app.postprocess import clean_line, clean_text

SAMPLE = """ORNEK AKARYAKIT A.S.
VERGI DAIRESI: KIZILAY
VKN/TCKN: 1234567890
TARIH: 25.11.2026 SAAT: 14:32
FIS NO: A0042
POMPA NO: 3
PLAKA: 06ABC123
KURSUNSUZ 95   35,40 LT   1.420,55
KDV %20   236,76
TOPLAM   1420,55
NAKIT   1420,55
"""


def test_extracts_known_turkish_receipt_fields():
    fields = extract_fields(SAMPLE)

    assert fields["tax_id"] == "1234567890"
    assert fields["tax_office"] == "KIZILAY"
    assert fields["date"] == "25.11.2026"
    assert fields["time"] == "14:32"
    assert fields["receipt_no"] == "A0042"
    assert fields["pump_no"] == "3"
    assert fields["plate"] == "06ABC123"
    assert fields["vat"] == "236,76"
    assert fields["total"] == "1420,55"
    assert fields["cash"] == "1420,55"


def test_total_guess_falls_back_to_last_amount():
    fields = extract_fields("EKMEK 12,50\nSUT 28,00")

    assert "total" not in fields
    assert fields["total_guess"] == "28,00"


def test_clean_line_normalises_prices_and_junk():
    assert clean_line("  TOPLAM  ~~ 12.50 ") == "TOPLAM 12,50"


def test_clean_line_leaves_dates_alone():
    assert clean_line("TARIH: 25.11.2026 SAAT: 14:32") == "TARIH: 25.11.2026 SAAT: 14:32"


def test_clean_text_drops_one_character_noise_lines():
    assert clean_text("A\nAB\n\n|\nABC") == "AB\nABC"
