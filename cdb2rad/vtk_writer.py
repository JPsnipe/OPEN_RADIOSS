"""Simple VTK writer for the web viewer."""
from typing import Dict, List, Tuple


def write_vtk(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
) -> None:
    """Write an ASCII VTK UnstructuredGrid file."""
    # map node ids to 0-based indices
    id_map = {nid: i for i, nid in enumerate(sorted(nodes))}

    with open(outfile, "w") as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write("cdb2rad mesh\n")
        f.write("ASCII\n")
        f.write("DATASET UNSTRUCTURED_GRID\n")
        f.write(f"POINTS {len(nodes)} float\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{x} {y} {z}\n")

        total = sum(len(e[2]) + 1 for e in elements)
        f.write(f"\nCELLS {len(elements)} {total}\n")
        for _, _, nids in elements:
            mapped = [id_map[n] for n in nids if n in id_map]
            f.write(str(len(mapped)) + " " + " ".join(str(i) for i in mapped) + "\n")

        f.write(f"\nCELL_TYPES {len(elements)}\n")
        for _, _, nids in elements:
            l = len(nids)
            if l == 3:
                ctype = 5  # TRIANGLE
            elif l == 4:
                ctype = 9  # QUAD
            elif l in (8, 20):
                ctype = 12  # HEXAHEDRON
            elif l == 10:
                ctype = 10  # TETRA
            else:
                ctype = 7  # POLYGON
            f.write(f"{ctype}\n")

