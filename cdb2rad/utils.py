"""Utility helpers for analyzing elements."""

from typing import List, Tuple, Dict
import json
from pathlib import Path


def element_summary(
    elements: List[Tuple[int, int, List[int]]],
    mapping_file: str | None = None,
) -> tuple[Dict[int, int], Dict[str, int]]:
    """Return counts by Ansys ``etype`` and Radioss keyword.

    Parameters
    ----------
    elements : list of tuples
        Sequence ``(eid, etype, node_ids)`` from :func:`parse_cdb`.
    mapping_file : str, optional
        Path to ``mapping.json``. When ``None`` uses the file next to this
        module.

    Returns
    -------
    tuple
        ``(etype_counts, keyword_counts)`` dictionaries.
    """
    if mapping_file is None:
        mapping_path = Path(__file__).with_name("mapping.json")
    else:
        mapping_path = Path(mapping_file)

    with open(mapping_path, "r", encoding="utf-8") as mf:
        mapping: Dict[str, str] = json.load(mf)

    etype_counts: Dict[int, int] = {}
    keyword_counts: Dict[str, int] = {}
    for _eid, etype, nids in elements:
        etype_counts[etype] = etype_counts.get(etype, 0) + 1
        key = mapping.get(str(etype))
        if not key:
            if len(nids) in (4, 3):
                key = "SHELL"
            elif len(nids) in (8, 20):
                key = "BRICK"
            elif len(nids) in (4, 10):
                key = "TETRA"
            else:
                key = "UNKNOWN"
        keyword_counts[key] = keyword_counts.get(key, 0) + 1

    return etype_counts, keyword_counts


def extract_material_block(rad_file: str) -> List[str]:
    """Extract material definition lines from a ``.rad`` file.

    The function looks for the first line starting with ``/MAT/`` and
    collects subsequent lines until a new block starts (``/FAIL`` or
    ``/END``).
    """

    block: List[str] = []
    recording = False
    with open(rad_file, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.lstrip()
            if stripped.startswith("/MAT/"):
                recording = True
            if recording:
                block.append(line.rstrip("\n"))
                if stripped.startswith("/FAIL") or stripped.startswith("/END"):
                    break
    return block
