"""Simple VTK writers for the web viewer."""
from typing import Dict, List, Tuple

try:  # optional dependency for XML output
    import vtk  # type: ignore
except Exception:  # pragma: no cover - optional
    vtk = None


def write_vtk(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
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

        if node_sets:
            f.write(f"\nPOINT_DATA {len(nodes)}\n")
            for name, ids in node_sets.items():
                arr = ["1" if nid in ids else "0" for nid in sorted(nodes)]
                f.write(f"SCALARS {name} int 1\n")
                f.write("LOOKUP_TABLE default\n")
                f.write("\n".join(arr) + "\n")

        if elem_sets:
            f.write(f"\nCELL_DATA {len(elements)}\n")
            for name, ids in elem_sets.items():
                arr = ["1" if eid in ids else "0" for eid, _, _ in elements]
                f.write(f"SCALARS {name} int 1\n")
                f.write("LOOKUP_TABLE default\n")
                f.write("\n".join(arr) + "\n")


def write_vtp(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
) -> None:
    """Write a VTK PolyData ``.vtp`` file.

    Requires :mod:`vtk`. Elements are exported as polygons so both surface and
    solid meshes can be visualised. When ``vtk`` is not available a
    :class:`ModuleNotFoundError` is raised.
    """

    if vtk is None:  # pragma: no cover - optional dependency
        raise ModuleNotFoundError("vtk is required to write .vtp files")

    id_map = {nid: i for i, nid in enumerate(sorted(nodes))}

    points = vtk.vtkPoints()
    for nid in sorted(nodes):
        x, y, z = nodes[nid]
        points.InsertNextPoint(x, y, z)

    polys = vtk.vtkCellArray()
    for _, _, nids in elements:
        if len(nids) < 3:
            continue
        ids = vtk.vtkIdList()
        for nid in nids:
            if nid in id_map:
                ids.InsertNextId(id_map[nid])
        polys.InsertNextCell(ids)

    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(polys)

    if node_sets:
        for name, ids in node_sets.items():
            arr = vtk.vtkIntArray()
            arr.SetName(name)
            arr.SetNumberOfTuples(len(nodes))
            arr.FillComponent(0, 0)
            for i, nid in enumerate(sorted(nodes)):
                if nid in ids:
                    arr.SetTuple1(i, 1)
            poly.GetPointData().AddArray(arr)

    if elem_sets:
        for name, ids in elem_sets.items():
            arr = vtk.vtkIntArray()
            arr.SetName(name)
            arr.SetNumberOfTuples(len(elements))
            arr.FillComponent(0, 0)
            for i, (eid, _, _) in enumerate(elements):
                if eid in ids:
                    arr.SetTuple1(i, 1)
            poly.GetCellData().AddArray(arr)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outfile)
    writer.SetInputData(poly)
    writer.Write()

