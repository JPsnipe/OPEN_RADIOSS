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
    """Write an ASCII VTK UnstructuredGrid file including optional groups."""
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
            for name, nids in node_sets.items():
                f.write(f"SCALARS {name} int 1\n")
                f.write("LOOKUP_TABLE default\n")
                nid_set = set(nids)
                for nid in sorted(nodes):
                    f.write(f"{1 if nid in nid_set else 0}\n")

                f.write("\n")


        if elem_sets:
            f.write(f"\nCELL_DATA {len(elements)}\n")
            for name, eids in elem_sets.items():
                f.write(f"SCALARS {name} int 1\n")
                f.write("LOOKUP_TABLE default\n")
                eid_set = set(eids)
                for eid, _, _ in elements:
                    f.write(f"{1 if eid in eid_set else 0}\n")

                f.write("\n")


def write_vtp(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
) -> None:
    """Write a VTK PolyData ``.vtp`` file including optional groups.

    Requires :mod:`vtk`. Elements are exported as polygons so both surface and
    solid meshes can be visualised. When ``vtk`` is not available a
    :class:`ModuleNotFoundError` is raised.
    """

    if vtk is None:  # pragma: no cover - optional dependency
        # Minimal fallback writer when VTK is unavailable
        id_map = {nid: i for i, nid in enumerate(sorted(nodes))}
        with open(outfile, "w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<VTKFile type="PolyData" version="0.1">\n')
            f.write('<PolyData>\n')
            f.write(
                f'<Piece NumberOfPoints="{len(nodes)}" NumberOfPolys="{len(elements)}">\n'
            )
            f.write('<Points>\n')
            f.write('<DataArray type="Float32" NumberOfComponents="3" format="ascii">\n')
            for nid in sorted(nodes):
                x, y, z = nodes[nid]
                f.write(f"{x} {y} {z} ")
            f.write('\n</DataArray>\n</Points>\n')
            f.write('<Polys>\n')
            f.write('<DataArray type="Int32" Name="connectivity" format="ascii">\n')
            for _, _, nids in elements:
                mapped = [str(id_map[n]) for n in nids if n in id_map]
                f.write(" ".join(mapped) + " ")
            f.write('\n</DataArray>\n')
            f.write('<DataArray type="Int32" Name="offsets" format="ascii">\n')
            offset = 0
            for _, _, nids in elements:
                offset += len([n for n in nids if n in id_map])
                f.write(f"{offset} ")
            f.write('\n</DataArray>\n')
            f.write('</Polys>\n')
            if node_sets:
                f.write('<PointData>\n')
                for name, nids in node_sets.items():
                    nid_set = set(nids)
                    f.write(
                        f'<DataArray type="Int32" Name="{name}" format="ascii">\n'
                    )
                    vals = ["1" if nid in nid_set else "0" for nid in sorted(nodes)]
                    f.write(" ".join(vals))
                    f.write('\n</DataArray>\n')
                f.write('</PointData>\n')
            if elem_sets:
                f.write('<CellData>\n')
                for name, eids in elem_sets.items():
                    eid_set = set(eids)
                    f.write(
                        f'<DataArray type="Int32" Name="{name}" format="ascii">\n'
                    )
                    vals = [
                        "1" if eid in eid_set else "0" for eid, _, _ in elements
                    ]
                    f.write(" ".join(vals))
                    f.write('\n</DataArray>\n')
                f.write('</CellData>\n')
            f.write('</Piece>\n</PolyData>\n</VTKFile>\n')
        return

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
        for name, nids in node_sets.items():
            arr = vtk.vtkIntArray()
            arr.SetName(name)
            for nid in sorted(nodes):
                arr.InsertNextValue(1 if nid in set(nids) else 0)
            poly.GetPointData().AddArray(arr)

    if elem_sets:
        for name, eids in elem_sets.items():
            arr = vtk.vtkIntArray()
            arr.SetName(name)
            for eid, _, _ in elements:
                arr.InsertNextValue(1 if eid in set(eids) else 0)
            poly.GetCellData().AddArray(arr)

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outfile)
    writer.SetInputData(poly)
    writer.Write()

