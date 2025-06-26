"""Utility to convert mesh files to VTK format for ParaViewWeb."""
from pathlib import Path
from typing import Dict, List, Tuple

import meshio

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

    mesh = meshio.read(infile)
    meshio.write(outfile, mesh)
