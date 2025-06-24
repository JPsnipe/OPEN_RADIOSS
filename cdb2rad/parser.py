"""Parser for .cdb files."""

from typing import Dict, List, Tuple


def parse_cdb(filepath: str) -> Tuple[Dict[int, List[float]], List[Tuple[int, str, List[int]]]]:
    """Parse a simple .cdb file.

    Parameters
    ----------
    filepath : str
        Path to the .cdb file.

    Returns
    -------
    Tuple containing:
    - nodes: dict mapping node id to coordinates [x, y, z]
    - elements: list of tuples (element id, element type, [node ids])
    """
    nodes: Dict[int, List[float]] = {}
    elements: List[Tuple[int, str, List[int]]] = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if parts[0].upper() == 'NODE' and len(parts) >= 5:
                nid = int(parts[1])
                coords = list(map(float, parts[2:5]))
                nodes[nid] = coords
            elif parts[0].upper() == 'ELEM' and len(parts) >= 5:
                eid = int(parts[1])
                etype = parts[2]
                node_ids = list(map(int, parts[3:]))
                elements.append((eid, etype, node_ids))

    return nodes, elements
