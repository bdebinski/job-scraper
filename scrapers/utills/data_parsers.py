import re
from markdownify import markdownify as md


def clean_job_description(html_content: str) -> str:
    if not html_content:
        return ""

    text = md(html_content, strip=["a", "img", "script", "style"], heading_style="ATX")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]

    return "\n".join(lines).strip()


def extract_salary_pln(employment_types: list) -> str:
    """Wyciąga pensję z priorytetem dla PLN."""
    if not employment_types:
        return "Nie podano"

    # Szukamy ofert w PLN
    pln_offer = next(
        (t for t in employment_types if t.get("currency", "").lower() == "pln"), None
    )

    # Jeśli nie ma PLN, bierzemy pierwszą lepszą (np. EUR)
    selected = pln_offer if pln_offer else employment_types[0]

    low = selected.get("from")
    high = selected.get("to")
    curr = selected.get("currency", "").upper()

    if low and high:
        return f"{low} - {high} {curr}"
    elif low:
        return f"{low}+ {curr}"

    return "Nie podano"
