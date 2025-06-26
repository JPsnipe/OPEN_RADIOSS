"""Lightweight validator for Radioss ``.rad`` files.

The checks implemented here focus on the subset of keywords that the
``writer_rad`` module generates.  Each block is validated using simple
patterns derived from the *Altair Radioss Reference Guide*.  The goal is not
to fully parse the file, but to detect obvious formatting mistakes that could
prevent OpenRadioss from running.
"""

from __future__ import annotations

import re


# Common numeric token (integer or float)
_NUM = r"[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?"
_num_re = re.compile(f"^{_NUM}$")

KEYWORDS = (
    "/BEGIN",
    "/END",
    "/PART",
    "/PROP",
    "/PRINT",
    "/RUN",
    "/STOP",
    "/TFILE",
    "/VERS",
    "/DT/NODA/CST/0",
    "/ANIM/DT",
    "/H3D/DT",
    "/ANIM",
    "/RFILE",
    "/ADYREL",
    "/MAT/",
    "/FAIL/",
    "/TITLE",
    "/BCS/",
    "/BOUNDARY/PRESCRIBED_MOTION",
    "/GRNOD/NODE/",
    "/INTER/TYPE",
    "/FRICTION",
    "/IMPVEL",
    "/GRAVITY",
    "/INCLUDE",
    "/NODE",
    "/GRNOD/GRNOD/",
    "/GRNOD/BOX/",
    "/BOX/RECTA/",
    "/RBODY/",
    "/RBE2/",
    "/RBE3/",
    "/TH/",
    "/FUNCT/",
    "/SUBSET/",
)


def _starts_with_keyword(text: str) -> bool:
    """Return ``True`` if the line starts with a known Radioss keyword."""
    for kw in KEYWORDS:
        if text.startswith(kw):
            return True
    return False


def _is_number(text: str) -> bool:
    return bool(_num_re.fullmatch(text))


def _validate_grnod(lines: list[str], idx: int) -> int:
    """Validate a ``/GRNOD/NODE`` block starting at ``idx``."""
    if idx + 1 >= len(lines):
        raise ValueError("Incomplete /GRNOD block")
    if not lines[idx + 1].strip():
        raise ValueError("Missing GRNOD name")
    i = idx + 2
    while i < len(lines):
        t = lines[i].strip()
        if not t or t.startswith("#"):
            i += 1
            continue
        if t.startswith("/"):
            break
        if not t.isdigit():
            raise ValueError(f"Invalid node id: {t}")
        i += 1
    return i - 1


def _validate_subset(lines: list[str], idx: int) -> int:
    """Validate a ``/SUBSET`` block starting at ``idx``."""
    if idx + 1 >= len(lines):
        raise ValueError("Incomplete /SUBSET block")
    if not lines[idx + 1].strip():
        raise ValueError("Missing subset name")
    i = idx + 2
    while i < len(lines):
        t = lines[i].strip()
        if not t or t.startswith("#"):
            i += 1
            continue
        if t.startswith("/"):
            break
        for tok in t.split():
            if not tok.isdigit():
                raise ValueError(f"Invalid subset id: {tok}")
        i += 1
    return i - 1


def validate_rad_format(filepath: str) -> None:
    """Validate the structure of ``filepath``.

    The function raises ``ValueError`` if an unexpected keyword or malformed
    block is found. Only the subset of Radioss cards emitted by this project is
    recognised.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [ln.rstrip() for ln in f]

    if not any(l.startswith("/") for l in lines):
        raise ValueError("No Radioss keywords found")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        if line.startswith("#include"):
            i += 1
            continue

        if line.startswith("/BCS/"):
            if i + 3 >= len(lines):
                raise ValueError("Incomplete /BCS block")
            if not lines[i + 1].strip():
                raise ValueError("BCS name missing")
            if not lines[i + 2].startswith("#"):
                raise ValueError("BCS header missing")
            nums = lines[i + 3].split()
            if len(nums) < 4 or not nums[0].isdigit():
                raise ValueError("Invalid /BCS data")
            i += 4
            continue

        if line.startswith("/BOUNDARY/PRESCRIBED_MOTION"):
            if i + 4 >= len(lines):
                raise ValueError("Incomplete prescribed motion block")
            if not lines[i + 1].strip():
                raise ValueError("Motion name missing")
            if not lines[i + 2].startswith("#"):
                raise ValueError("Prescribed motion header missing")
            if not _is_number(lines[i + 4].split()[0]):
                raise ValueError("Invalid prescribed motion value")
            i += 5
            continue

        if line.startswith("/INTER/TYPE7"):
            if i + 4 >= len(lines):
                raise ValueError("Incomplete TYPE7 block")
            if not lines[i + 3].startswith("/FRICTION"):
                raise ValueError("TYPE7 missing /FRICTION")
            i += 5
            continue

        if line.startswith("/INTER/TYPE2"):
            if i + 3 >= len(lines):
                raise ValueError("Incomplete TYPE2 block")
            if not lines[i + 2].startswith("/FRICTION"):
                raise ValueError("TYPE2 missing /FRICTION")
            i += 4
            continue

        if line.startswith("/RBODY/"):
            if i + 7 >= len(lines):
                raise ValueError("Incomplete /RBODY block")
            i += 8
            continue

        if line.startswith("/RBE2/"):
            if i + 4 >= len(lines):
                raise ValueError("Incomplete /RBE2 block")
            i += 5
            continue

        if line.startswith("/RBE3/"):
            if i + 5 >= len(lines):
                raise ValueError("Incomplete /RBE3 block")
            i += 6
            continue

        if line.startswith("/SUBSET/"):
            i = _validate_subset(lines, i)
            i += 1
            continue


        if line.startswith("/GRNOD/NODE/"):
            i = _validate_grnod(lines, i)
            i += 1
            continue

        if line.startswith("/GRAVITY"):
            if i + 2 >= len(lines):
                raise ValueError("Incomplete /GRAVITY block")
            if len(lines[i + 1].split()) != 2:
                raise ValueError("/GRAVITY header format")
            if not all(_is_number(t) for t in lines[i + 2].split()):
                raise ValueError("Invalid gravity vector")
            i += 3
            continue

        if line.startswith("/"):
            if not _starts_with_keyword(line.split()[0]):
                raise ValueError(f"Unknown keyword: {line}")
            i += 1
            continue

        # plain text or numeric line
        tokens = line.split()
        if all(_is_number(t) for t in tokens):
            i += 1
            continue
        allowed = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._+-/ (),"
        )
        if not set(line).issubset(allowed):
            raise ValueError(f"Invalid characters: {line}")
        i += 1
