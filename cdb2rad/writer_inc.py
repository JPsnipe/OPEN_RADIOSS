"""Utilities to write ``mesh.inp`` include files in Radioss format."""

from typing import Dict, List, Tuple
import json
from pathlib import Path


def write_mesh_inp(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mapping_file: str | None = None,
) -> None:
    """Write ``mesh.inp`` with element blocks derived from ``mapping.json``."""

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
            # Fallback based on node count
            if len(nids) in (4, 3):
                key = "SHELL"
            elif len(nids) in (8, 20):
                key = "BRICK"
            elif len(nids) in (4, 10):
                key = "TETRA"
            else:
                continue
        categorized.setdefault(key, []).append((eid, nids))

    with open(outfile, "w") as f:
        f.write("/NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid:10d}{x:15.6f}{y:15.6f}{z:15.6f}\n")

        for key, items in categorized.items():
            f.write(f"\n/{key}\n")
            for eid, nids in items:
                line = f"{eid:10d}" + "".join(f"{nid:10d}" for nid in nids)
                f.write(line + "\n")
