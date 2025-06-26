"""Utility functions to convert various mesh formats to VTK."""
from __future__ import annotations

from pathlib import Path

try:  # Optional dependency
    import meshio
except ImportError:  # pragma: no cover - graceful handling
    meshio = None  # type: ignore

from .parser import parse_cdb
from .vtk_writer import write_vtk


SUPPORTED_EXT = {".cdb", ".inp", ".rad", ".inc", ".vtk", ".vtp", ".stl", ".obj"}


def convert_to_vtk(infile: str, outfile: str) -> None:
    """Convert ``infile`` to VTK format at ``outfile``.

    If ``infile`` is a ``.cdb`` it is parsed using :func:`parse_cdb`. Other
    formats are handled via :mod:`meshio`.
    """
    ext = Path(infile).suffix.lower()
    if ext == ".cdb":
        nodes, elements, *_ = parse_cdb(infile)
        write_vtk(nodes, elements, outfile)
        return
    if meshio is None:
        raise ModuleNotFoundError(
            "meshio is required to convert meshes in formats other than .cdb"
        )
    mesh = meshio.read(infile)
    meshio.write(outfile, mesh)
