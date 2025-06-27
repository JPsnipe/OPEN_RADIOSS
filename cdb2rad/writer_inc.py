"""Utilities to write ``mesh.inc`` include files in Radioss format."""

from typing import Dict, List, Tuple
import json
from pathlib import Path

# Material definitions used to be written here, which duplicated them between
# ``mesh.inc`` and the starter file.  That logic now lives in ``writer_rad``,
# so this module no longer outputs material blocks.


def write_mesh_inc(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mapping_file: str | None = None,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
    materials: Dict[int, Dict[str, float]] | None = None,
) -> None:
    """Write ``mesh.inc`` with element blocks derived from ``mapping.json``.

    Parameters other than ``nodes`` and ``elements`` are optional.  Material
    definitions supplied via ``materials`` are ignored and kept only for
    backward compatibility.

    Node and element sets (from ``CMBLOCK``) can be written for later use in
    the starter file.  Material definitions are handled exclusively by
    ``write_starter``.
    """

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

        if node_sets:
            for idx, (name, nids) in enumerate(node_sets.items(), start=1):
                f.write(f"\n/GRNOD/NODE/{idx}\n")
                f.write(f"{name}\n")
                for nid in nids:
                    f.write(f"{nid:10d}\n")

        if elem_sets:
            for idx, (name, eids) in enumerate(elem_sets.items(), start=1):
                f.write(f"\n/SET/EL/{idx}\n")
                f.write(f"{name}\n")
                for eid in eids:
                    f.write(f"{eid:10d}\n")

        # Materials are intentionally not written in mesh.inc files.
        # They are instead handled exclusively by ``writer_rad`` when
        # generating the starter.  The ``materials`` argument is kept for
        # backward compatibility but is ignored.
