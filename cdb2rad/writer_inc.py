"""Utilities to write mesh.inc files."""
from typing import Dict, List, Tuple


def write_mesh_inc(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, str, List[int]]],
    outfile: str,
) -> None:
    """Write mesh.inc containing /NODE and /SHELL blocks."""
    with open(outfile, 'w') as f:
        f.write('/NODE\n')
        for nid, coords in nodes.items():
            f.write(f'{nid}, {coords[0]}, {coords[1]}, {coords[2]}\n')

        f.write('\n/SHELL\n')
        for eid, etype, nids in elements:
            if etype.upper() == 'SHELL':
                node_list = ', '.join(str(n) for n in nids)
                f.write(f'{eid}, {node_list}\n')
