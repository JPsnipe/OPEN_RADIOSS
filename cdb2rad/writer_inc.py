"""Utilities to write ``mesh.inp`` include files in Radioss format."""

from typing import Dict, List, Tuple


def write_mesh_inp(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
) -> None:
    """Write ``mesh.inp`` containing ``/NODE``, ``/SHELL`` and ``/BRICK`` blocks."""

    shells = [e for e in elements if len(e[2]) == 4]
    bricks = [e for e in elements if len(e[2]) == 8]

    with open(outfile, "w") as f:
        f.write("/NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid:10d}{x:15.6f}{y:15.6f}{z:15.6f}\n")

        if shells:
            f.write("\n/SHELL\n")
            for eid, _etype, nids in shells:
                values = [f"{eid:10d}"] + [f"{nid:10d}" for nid in nids]
                f.write("".join(values) + "\n")

        if bricks:
            f.write("\n/BRICK\n")
            for eid, _etype, nids in bricks:
                values = [f"{eid:10d}"] + [f"{nid:10d}" for nid in nids]
                f.write("".join(values) + "\n")
