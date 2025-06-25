import io
from functools import lru_cache
from typing import List

import requests
from PyPDF2 import PdfReader

REFERENCE_GUIDE = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_ReferenceGuide.pdf"
)
THEORY_MANUAL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_TheoryManual.pdf"
)


@lru_cache(maxsize=2)
def _fetch_pdf(url: str) -> str:
    """Download and extract text from the given PDF URL."""
    resp = requests.get(url)
    resp.raise_for_status()
    reader = PdfReader(io.BytesIO(resp.content))
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)


def search_pdf(url: str, query: str, max_hits: int = 5) -> List[str]:
    """Return up to ``max_hits`` lines containing the query from the PDF."""
    content = _fetch_pdf(url)
    results: List[str] = []
    q = query.lower()
    for line in content.splitlines():
        if q in line.lower():
            line = line.strip()
            if line:
                results.append(line)
            if len(results) >= max_hits:
                break
    return results
