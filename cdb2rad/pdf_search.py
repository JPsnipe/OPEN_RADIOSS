import io
from functools import lru_cache
from typing import List
from pathlib import Path

import requests

try:  # PyPDF2 is optional
    from PyPDF2 import PdfReader  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled in search_pdf
    PdfReader = None

REFERENCE_GUIDE_URL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_ReferenceGuide.pdf"
)
THEORY_MANUAL_URL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_TheoryManual.pdf"
)
USER_GUIDE_URL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_UserGuide.pdf"
)

DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
REFERENCE_GUIDE = DOCS_DIR / "AltairRadioss_2022_ReferenceGuide.pdf"
THEORY_MANUAL = DOCS_DIR / "AltairRadioss_2022_TheoryManual.pdf"
USER_GUIDE = DOCS_DIR / "AltairRadioss_2022_UserGuide.pdf"


@lru_cache(maxsize=2)
def _fetch_pdf(source: str | Path) -> str:
    """Return the text content of ``source`` which can be a URL or file."""
    if PdfReader is None:
        raise ImportError("PyPDF2 is required for PDF search")

    if isinstance(source, (str, Path)) and Path(str(source)).exists():
        with open(source, "rb") as fh:
            data = fh.read()
    else:
        resp = requests.get(str(source))
        resp.raise_for_status()
        data = resp.content

    reader = PdfReader(io.BytesIO(data))
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n".join(text_parts)


def search_pdf(source: str | Path, query: str, max_hits: int = 5) -> List[str]:
    """Return up to ``max_hits`` lines containing ``query`` in the PDF."""
    content = _fetch_pdf(source)
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
