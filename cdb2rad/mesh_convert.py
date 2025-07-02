
"""Utility functions to convert various mesh formats to VTK."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import tempfile

try:  # Optional dependency
    import meshio
except ImportError:  # pragma: no cover - graceful handling
    meshio = None  # type: ignore


from .parser import parse_cdb
from .vtk_writer import write_vtk, write_vtp


SUPPORTED_EXT = {".cdb", ".inp", ".rad", ".inc", ".vtk", ".vtp", ".stl", ".obj"}


def convert_to_vtk(infile: str, outfile: str) -> None:
    """Convert ``infile`` to VTK format at ``outfile``.

    If ``infile`` is a ``.cdb`` it is parsed using :func:`parse_cdb`. Other
    formats are handled via :mod:`meshio`.
    """
    ext = Path(infile).suffix.lower()
    if ext == ".cdb":
        nodes, elements, node_sets, elem_sets, _ = parse_cdb(infile)
        write_vtk(
            nodes,
            elements,
            outfile,
            node_sets=node_sets,
            elem_sets=elem_sets,
        )
        return

    if meshio is None:
        raise ModuleNotFoundError(
            "meshio is required to convert meshes in formats other than .cdb"
        )

    mesh = meshio.read(infile)
    meshio.write(outfile, mesh)


def mesh_to_temp_vtk(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    suffix: str = ".vtk",
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
) -> str:
    """Return path to a temporary VTK/VTP file with optional groups."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    if suffix.endswith(".vtp"):
        write_vtp(nodes, elements, tmp.name, node_sets=node_sets, elem_sets=elem_sets)
    else:
        write_vtk(nodes, elements, tmp.name, node_sets=node_sets, elem_sets=elem_sets)
    return tmp.name
