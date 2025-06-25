#!/usr/bin/env python
"""Download Altair Radioss documentation PDFs for offline use."""

import argparse
from pathlib import Path
import requests

REFERENCE_GUIDE_URL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_ReferenceGuide.pdf"
)
THEORY_MANUAL_URL = (
    "https://2022.help.altair.com/2022/simulation/pdfs/radopen/"
    "AltairRadioss_2022_TheoryManual.pdf"
)

PDFS = {
    REFERENCE_GUIDE_URL: "AltairRadioss_2022_ReferenceGuide.pdf",
    THEORY_MANUAL_URL: "AltairRadioss_2022_TheoryManual.pdf",
}


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"{dest} already exists")
        return
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=8192):
            fh.write(chunk)
    print(f"Downloaded {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="docs", help="Destination directory")
    args = parser.parse_args()
    out_dir = Path(args.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for url, name in PDFS.items():
        download(url, out_dir / name)


if __name__ == "__main__":
    main()
