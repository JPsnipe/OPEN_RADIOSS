"""Write Abaqus ``.inp`` files from parsed CDB data.

This module provides a minimal exporter that converts nodes and elements
from the internal representation to a basic Abaqus input deck. Only
geometry and named sets are handled; materials are intentionally ignored.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import json
from pathlib import Path
import os


def _write_id_list(f, ids: List[int], per_line: int = 16) -> None:
    """Write integer ``ids`` separated by commas and wrapped at ``per_line``."""
    for i in range(0, len(ids), per_line):
        line = ", ".join(str(n) for n in ids[i : i + per_line])
        f.write(line + "\n")


def write_inp(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mapping_file: str | None = None,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
) -> None:
    """Write ``outfile`` in Abaqus ``.inp`` format without materials."""

    if mapping_file is None:
        mapping_path = Path(__file__).with_name("mapping.json")
    else:
        mapping_path = Path(mapping_file)

    with open(mapping_path, "r", encoding="utf-8") as mf:
        mapping: Dict[str, str] = json.load(mf)

    categorized: Dict[str, List[Tuple[int, List[int]]]] = {}
    for eid, etype, nids in elements:
        key = mapping.get(str(etype))
        if not key:
            if len(nids) in (4, 3):
                key = "SHELL"
            elif len(nids) in (8, 20):
                key = "BRICK"
            elif len(nids) in (4, 10):
                key = "TETRA"
            else:
                continue
        categorized.setdefault(key, []).append((eid, nids))

    type_map = {
        "SHELL": {4: "S4", 3: "S3"},
        "BRICK": {8: "C3D8", 20: "C3D20"},
        "TETRA": {4: "C3D4", 10: "C3D10"},
    }

    with open(outfile, "w") as f:
        f.write("*NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid}, {x:.6f}, {y:.6f}, {z:.6f}\n")

        for key, items in categorized.items():
            if not items:
                continue
            n_count = len(items[0][1])
            abaqus_type = type_map.get(key, {}).get(n_count, "C3D8")
            f.write(f"\n*ELEMENT, TYPE={abaqus_type}\n")
            for eid, nids in items:
                line = ", ".join(str(n) for n in nids)
                f.write(f"{eid}, {line}\n")

        if node_sets:
            for name, ids in node_sets.items():
                f.write(f"\n*NSET, NSET={name}\n")
                _write_id_list(f, ids)

        if elem_sets:
            for name, ids in elem_sets.items():
                f.write(f"\n*ELSET, ELSET={name}\n")
                _write_id_list(f, ids)

    os.chmod(outfile, 0o644)
