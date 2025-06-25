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


def check_rad_inputs(
    use_cdb_mats: bool,
    materials: Dict[int, Dict[str, float]] | None,
    use_impact: bool,
    impact_materials: List[Dict[str, float]] | None,
    bcs: List[Dict[str, object]] | None,
    interfaces: List[Dict[str, object]] | None,
) -> List[str]:
    """Return a list of missing configuration items for RAD generation."""
    errors: List[str] = []
    if use_cdb_mats and not materials:
        errors.append("Faltan materiales importados del CDB")
    if use_impact and not impact_materials:
        errors.append("No se han definido materiales de impacto")
    if bcs:
        for idx, bc in enumerate(bcs, start=1):
            if not bc.get("nodes"):
                errors.append(f"BC {idx} sin nodos")
                break
    if interfaces:
        for idx, itf in enumerate(interfaces, start=1):
            if not itf.get("slave") or not itf.get("master"):
                errors.append(f"Interfaz {idx} incompleta")
                break
    return errors
