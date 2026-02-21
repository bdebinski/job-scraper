import re
from typing import Any
from markdownify import markdownify as md


def clean_job_description(html_content: str) -> str:
    """
    Removes html tags, new lines from text, then converts text to markdowns.
    """
    if not html_content:
        return ""

    text = md(html_content, strip=["a", "img", "script", "style"], heading_style="ATX")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]

    return "\n".join(lines).strip()


def extract_salary_pln(employment_types: list[dict[str, Any]]) -> str:
    """Extracts salary in PLN from JJIT fetch API."""
    if not employment_types:
        return "Not provided"

    pln_offer = next(
        (t for t in employment_types if t.get("currency", "").lower() == "pln"), None
    )

    selected = pln_offer if pln_offer else employment_types[0]

    low = selected.get("from")
    high = selected.get("to")
    curr = selected.get("currency", "").upper()

    if low and high:
        return f"{low} - {high} {curr}"
    elif low:
        return f"{low}+ {curr}"

    return "Not provided"
