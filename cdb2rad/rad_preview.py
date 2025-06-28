"""Utilities to preview Radioss cards as plain text.

These helpers return short strings matching the lines written to the final
``.rad`` file. Group definitions like ``/GRNOD`` or ``/SET`` are omitted to
keep the preview compact.
"""

from __future__ import annotations

from io import StringIO
from typing import Dict, List, Tuple, Any

from .writer_rad import (
    write_starter,
    write_engine,
    DEFAULT_THICKNESS,
    DEFAULT_E,
    DEFAULT_NU,
    DEFAULT_RHO,
)


_BASIC_NODES = {1: [0.0, 0.0, 0.0], 2: [1.0, 0.0, 0.0], 3: [1.0, 1.0, 0.0], 4: [0.0, 1.0, 0.0]}
_BASIC_ELEMS = [(1, 2, [1, 2, 3, 4])]


def _extract_block(text: str, start: str) -> str:
    lines = text.splitlines()
    out: List[str] = []
    capture = False
    for ln in lines:
        if ln.startswith(start):
            capture = True
        if capture:
            if ln.startswith("/GRNOD") or ln.startswith("/SET") or ln.startswith("/SUBSET"):
                out.append(ln)
                out.append("...")
                break
            out.append(ln)
            if ln.startswith("/") and ln != start and not ln.startswith("#"):
                break
    return "\n".join(out)


def preview_material(mat: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        materials={int(mat.get("id", 1)): mat},
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/MAT/")


def preview_property(prop: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        properties=[prop],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), f"/PROP/{prop.get('type','SHELL').upper()}")


def preview_part(part: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        parts=[part],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), f"/PART/{part.get('id',1)}")


def preview_bc(bc: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        boundary_conditions=[bc],
        include_inc=False,
        default_material=False,
    )
    key = "/BOUNDARY" if bc.get("type") else "/BCS/"
    return _extract_block(buf.getvalue(), key)


def preview_interface(itf: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        interfaces=[itf],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/INTER/")


def preview_rbody(rb: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        rbody=[rb],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/RBODY/")


def preview_rbe2(rb: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        rbe2=[rb],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/RBE2/")


def preview_rbe3(rb: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        rbe3=[rb],
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/RBE3/")


def preview_init_velocity(data: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        init_velocity=data,
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/IMPVEL/")


def preview_gravity(data: Dict[str, Any]) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        gravity=data,
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), "/GRAV")


def preview_subset(name: str, ids: List[int], idx: int) -> str:
    buf = StringIO()
    write_starter(
        _BASIC_NODES,
        _BASIC_ELEMS,
        buf,
        subsets={name: ids},
        include_inc=False,
        default_material=False,
    )
    return _extract_block(buf.getvalue(), f"/SUBSET/{idx}")


def preview_control(settings: Dict[str, Any]) -> str:
    buf = StringIO()
    write_engine(buf, **settings)
    text = buf.getvalue()
    lines = text.splitlines()
    return "\n".join(lines[1:])


