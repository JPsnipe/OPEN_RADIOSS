"""Parser for .cdb files."""

from typing import Dict, List, Tuple


def parse_cdb(filepath: str) -> Tuple[Dict[int, List[float]], List[Tuple[int, int, List[int]]]]:
    """Parse an Ansys ``.cdb`` file containing ``NBLOCK`` and ``EBLOCK``.

    The parser was originally written for a minimal comma separated ``.cdb``
    format.  Newer examples exported from Ansys use fixed width Fortran records
    with ``NBLOCK`` written as ``(3i9,6e21.13e3)`` and ``EBLOCK`` as
    ``(19i10)``.  This function supports both styles.  For NBLOCK only the
    first three coordinates are stored for each node.  For EBLOCK the element
    id and type are extracted together with the node connectivity.
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
            # optional format line e.g. (3i9,6e21.13e3)
            if i < len(lines) and lines[i].lstrip().startswith("("):
                i += 1
            while i < len(lines):
                ln = lines[i].rstrip("\n")
                if ln.strip().startswith("N,") or ln.strip().startswith("-1"):
                    break
                if not ln.strip():
                    i += 1
                    continue
                parts = [p for p in ln.split(";") if p]
                if len(parts) == 1 and "," in ln:
                    parts = ln.split(",")
                if len(parts) >= 4:
                    try:
                        nid = int(parts[0])
                        x, y, z = map(float, parts[1:4])
                        nodes[nid] = [x, y, z]
                        i += 1
                        continue
                    except ValueError:
                        pass
                # fallback to fixed width format
                while len(ln) < 90 and i + 1 < len(lines):
                    i += 1
                    ln += lines[i].rstrip("\n")
                if len(ln) >= 90:
                    try:
                        nid = int(ln[0:9])
                        x = float(ln[27:48])
                        y = float(ln[48:69])
                        z = float(ln[69:90])
                        nodes[nid] = [x, y, z]
                    except ValueError:
                        pass
                i += 1
        elif line.startswith("EBLOCK"):
            i += 1
            if i < len(lines) and lines[i].lstrip().startswith("("):
                i += 1
            while i < len(lines):
                ln = lines[i].rstrip("\n")
                if ln.strip().startswith("-1") or ln.strip().startswith("N,"):
                    break
                if not ln.strip():
                    i += 1
                    continue
                parts = [p for p in ln.split(";") if p]
                if len(parts) == 1 and "," in ln:
                    parts = ln.split(",")
                if len(parts) >= 3:
                    try:
                        eid = int(parts[0])
                        etype = int(parts[1])
                        node_ids = [int(p) for p in parts[2:] if p]
                        elements.append((eid, etype, node_ids))
                        i += 1
                        continue
                    except ValueError:
                        pass
                while len(ln) % 10 != 0 and i + 1 < len(lines):
                    i += 1
                    ln += lines[i].rstrip("\n")
                if len(ln) >= 110:  # at least header + 1 node
                    try:
                        vals = [int(ln[j:j+10]) for j in range(0, len(ln), 10)]
                        eid = vals[10]
                        etype = vals[1]
                        node_ids = vals[11:]
                        elements.append((eid, etype, node_ids))
                    except ValueError:
                        pass
                i += 1
        else:
            i += 1


    return nodes, elements
