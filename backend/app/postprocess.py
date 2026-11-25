import re

_JUNK = re.compile(r"[^\w\sÇĞIİÖŞÜçğıöşü:.,/()%*+\-₺]")
_SPACES = re.compile(r"\s+")
_PRICE = re.compile(r"(\d+)[.,](\d{2})(?![.,]?\d)")


def clean_line(line: str) -> str:
    line = _JUNK.sub("", line.strip())
    line = _PRICE.sub(r"\1,\2", line)
    return _SPACES.sub(" ", line).strip()


def clean_text(text: str) -> str:
    lines = (clean_line(line) for line in text.splitlines())
    return "\n".join(line for line in lines if len(line) >= 2)
