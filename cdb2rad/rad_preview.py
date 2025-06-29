"""Utilities to preview Radioss cards as plain text.

These helpers return short strings matching the lines written to the final
``.rad`` file. Group definitions like ``/GRNOD`` or ``/SET`` are omitted to
keep the preview compact.
"""

from __future__ import annotations

from io import StringIO
from typing import Dict, List, Any

from .writer_rad import write_starter, write_engine


_BASIC_NODES = {1: [0.0, 0.0, 0.0], 2: [1.0, 0.0, 0.0], 3: [1.0, 1.0, 0.0], 4: [0.0, 1.0, 0.0]}
_BASIC_ELEMS = [(1, 2, [1, 2, 3, 4])]


def _extract_block(text: str, start: str) -> str:
    """Return a short snippet starting at ``start`` until the next keyword."""

    lines = text.splitlines()
    out: List[str] = []
    capture = False
    skipping = False

    for i, ln in enumerate(lines):
        if ln.startswith(start):
            capture = True
        if not capture:
            continue

        if skipping:
            if ln.startswith("/FRICTION"):
                out.append("...")
                out.append(ln)
                if i + 1 < len(lines):
                    out.append(lines[i + 1])
                out.append("...")
                break
            continue

        out.append(ln)

        if ln.startswith("/GRNOD") or ln.startswith("/SET") or ln.startswith("/SUBSET"):
            skipping = True
            continue

        if ln.startswith("/FRICTION"):
            if i + 1 < len(lines):
                out.append(lines[i + 1])
            out.append("...")
            break

        if (
            ln.startswith("/")
            and not ln.startswith(start)
            and not ln.startswith("/FAIL")
            and not ln.startswith("#")
        ):
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
        auto_properties=False,
        auto_parts=False,
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
        default_material=True,
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
    bc_type = str(bc.get("type", "BCS")).upper()
    key = "/BOUNDARY" if bc_type != "BCS" else "/BCS/"
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


def preview_remote_point(rp: Dict[str, Any]) -> str:
    """Return ``/NODE`` lines for a remote point preview."""
    nid = int(rp.get("id", 0))
    x, y, z = rp.get("coords", (0.0, 0.0, 0.0))
    return f"/NODE\n{nid:10d}{x:15.6f}{y:15.6f}{z:15.6f}"


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
    ctrl_args = dict(settings)
    if "adyrel_start" in ctrl_args or "adyrel_stop" in ctrl_args:
        start = ctrl_args.pop("adyrel_start", None)
        stop = ctrl_args.pop("adyrel_stop", None)
        ctrl_args["adyrel"] = (start, stop)
    write_engine(buf, **ctrl_args)
    text = buf.getvalue()
    lines = text.splitlines()
    return "\n".join(lines[1:])


