import re

AMOUNT = r"([0-9]+[.,][0-9]{2})"
SEP = r"\s*[:=\-]?\s*"

PATTERNS: list[tuple[str, str]] = [
    ("total", rf"\bTOPLAM{SEP}{AMOUNT}"),
    ("vat", rf"\bKDV(?:\s*[%X]\s*\d+)?{SEP}{AMOUNT}"),
    ("cash", rf"\bNAK[İI]T{SEP}{AMOUNT}"),
    ("card", rf"\bK\.?\s*KART[İI]?{SEP}{AMOUNT}"),
    ("receipt_no", rf"\bF[İI][ŞS]\s*NO{SEP}([A-Z0-9]+)"),
    ("z_no", rf"\bZ\s*NO{SEP}([0-9]+)"),
    ("eku_no", rf"\bEK[ÜU]\s*NO{SEP}([0-9]+)"),
    ("pump_no", rf"\bPOMPA\s*NO{SEP}([0-9]+)"),
    ("plate", rf"\bPLAKA{SEP}([A-Z0-9\-]{{5,}})"),
    ("mersis_no", rf"\bMERS[İI]S\s*NO{SEP}([0-9]{{16}})"),
    ("tax_office", rf"\bVER[GĞ][İI]\s*DA[İI]RES[İI]{SEP}([A-ZÇĞİÖŞÜ]+)"),
    ("tax_id", rf"\b(?:VKN|TCKN|VKN/TCKN|V\.?D\.?\s*NO){SEP}([0-9]{{10,11}})"),
    ("date", r"\b([0-3][0-9][./][01][0-9][./][0-9]{4})\b"),
    ("time", r"\b([0-2][0-9]:[0-5][0-9])\b"),
]

_FALLBACK_AMOUNT = re.compile(r"\b([0-9]+,[0-9]{2})\b")


def extract_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, pattern in PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields[key] = match.group(1)
    if "total" not in fields:
        amounts = _FALLBACK_AMOUNT.findall(text)
        if amounts:
            fields["total_guess"] = amounts[-1]
    return fields
