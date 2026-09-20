import re


def normalize_column_name(name: str) -> str:
    """Turn messy headers into snake_case identifiers.

    Examples: "C.G.P.A" → "cgpa", "Reg No." → "reg_no".
    """
    text = name.strip().lower()
    text = text.replace("&", " and ")
    # Collapse dotted abbreviations like C.G.P.A before stripping punctuation.
    if re.fullmatch(r"(?:[a-z0-9]\.)+[a-z0-9]\.?", text.replace(" ", "")):
        text = re.sub(r"[^a-z0-9]", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "column"


def make_unique(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique: list[str] = []
    for name in names:
        base = name or "column"
        count = seen.get(base, 0) + 1
        seen[base] = count
        unique.append(base if count == 1 else f"{base}_{count}")
    return unique
