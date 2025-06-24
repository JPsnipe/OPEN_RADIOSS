"""Parser for .cdb files."""

from typing import Dict, List, Tuple


def parse_cdb(filepath: str) -> Tuple[Dict[int, List[float]], List[Tuple[int, int, List[int]]]]:
    """Parse an Ansys ``.cdb`` file containing ``NBLOCK`` and ``EBLOCK``.

    The parser is intentionally simple and expects that node and element
    definitions are comma separated. Only the node id and the first three
    coordinates are stored for each node. For elements, the first integer after
    the element id is considered the element type followed by the connectivity
    list. Lines starting with ``-1`` end the current block.
    """

    nodes: Dict[int, List[float]] = {}
    elements: List[Tuple[int, int, List[int]]] = []

    with open(filepath, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("NBLOCK"):
            i += 1
            while i < len(lines):
                ln = lines[i].strip()
                if ln.startswith("-1"):
                    break
                if ln:
                    parts = [p for p in ln.split(";") if p]
                    if len(parts) == 1:
                        parts = ln.split(",")
                    if len(parts) >= 4:
                        nid = int(parts[0])
                        try:
                            x, y, z = map(float, parts[1:4])
                        except ValueError:
                            i += 1
                            continue
                        nodes[nid] = [x, y, z]
                i += 1
        elif line.startswith("EBLOCK"):
            i += 1
            while i < len(lines):
                ln = lines[i].strip()
                if ln.startswith("-1"):
                    break
                if ln:
                    parts = [p for p in ln.split(";") if p]
                    if len(parts) == 1:
                        parts = ln.split(",")
                    if len(parts) >= 3:
                        eid = int(parts[0])
                        etype = int(parts[1])
                        node_ids = [int(p) for p in parts[2:] if p]
                        elements.append((eid, etype, node_ids))
                i += 1
        i += 1

    return nodes, elements
