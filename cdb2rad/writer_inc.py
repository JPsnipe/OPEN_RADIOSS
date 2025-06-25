"""Utilities to write ``mesh.inc`` include files in Radioss format."""

from typing import Dict, List, Tuple
import json
from pathlib import Path

from .material_defaults import apply_default_materials


def write_mesh_inc(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mapping_file: str | None = None,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
    materials: Dict[int, Dict[str, float]] | None = None,
) -> None:
    """Write ``mesh.inc`` with element blocks derived from ``mapping.json``.

    Optionally, node and element sets (from CMBLOCK) and basic material
    properties can be written for later use in the starter file.
    """

    if mapping_file is None:
        mapping_path = Path(__file__).with_name("mapping.json")
    else:
        mapping_path = Path(mapping_file)

    with open(mapping_path, "r", encoding="utf-8") as mf:
        mapping: Dict[str, str] = json.load(mf)

    categorized: Dict[str, List[Tuple[int, List[int]]]] = {}
    for eid, etype, nids in elements:
        key = mapping.get(str(etype))
        if not key:
            # Fallback based on node count
            if len(nids) in (4, 3):
                key = "SHELL"
            elif len(nids) in (8, 20):
                key = "BRICK"
            elif len(nids) in (4, 10):
                key = "TETRA"
            else:
                continue
        categorized.setdefault(key, []).append((eid, nids))

    with open(outfile, "w") as f:
        f.write("/NODE\n")
        for nid in sorted(nodes):
            x, y, z = nodes[nid]
            f.write(f"{nid:10d}{x:15.6f}{y:15.6f}{z:15.6f}\n")

        for key, items in categorized.items():
            f.write(f"\n/{key}\n")
            for eid, nids in items:
                line = f"{eid:10d}" + "".join(f"{nid:10d}" for nid in nids)
                f.write(line + "\n")

        if node_sets:
            for idx, (name, nids) in enumerate(node_sets.items(), start=1):
                f.write(f"\n/GRNOD/NODE/{idx}\n")
                f.write(f"{name}\n")
                for nid in nids:
                    f.write(f"{nid:10d}\n")

        if elem_sets:
            for idx, (name, eids) in enumerate(elem_sets.items(), start=1):
                f.write(f"\n/SET/EL/{idx}\n")
                f.write(f"{name}\n")
                for eid in eids:
                    f.write(f"{eid:10d}\n")

        if materials:
            materials = apply_default_materials(materials)
            for mid, props in materials.items():
                law = props.get("LAW", "LAW1").upper()
                e = props.get("EX", 210000.0)
                nu = props.get("NUXY", 0.3)
                rho = props.get("DENS", 7800.0)
                if law in ("LAW2", "JOHNSON_COOK", "PLAS_JOHNS"):
                    a = props.get("A", 0.0)
                    b = props.get("B", 0.0)
                    n_val = props.get("N", 0.0)
                    c = props.get("C", 0.0)
                    eps0 = props.get("EPS0", 1.0)
                    f.write(f"\n/MAT/LAW2/{mid}\n")
                    f.write(f"{rho} {e} {nu}\n")
                    f.write(f"{a} {b} {n_val} {c} {eps0}\n")
                elif law in ("LAW27", "PLAS_BRIT"):
                    sig0 = props.get("SIG0", 0.0)
                    su = props.get("SU", 0.0)
                    epsu = props.get("EPSU", 0.0)
                    f.write(f"\n/MAT/LAW27/{mid}\n")
                    f.write(f"{rho} {e} {nu}\n")
                    f.write(f"{sig0} {su} {epsu}\n")
                elif law in ("LAW36", "PLAS_TAB"):
                    fs = props.get("Fsmooth", 0.0)
                    fc = props.get("Fcut", 0.0)
                    ch = props.get("Chard", 0.0)
                    f.write(f"\n/MAT/LAW36/{mid}\n")
                    f.write(f"{rho} {e} {nu}\n")
                    f.write(f"{fs} {fc} {ch}\n")
                elif law in ("LAW44", "COWPER"):
                    a = props.get("A", 0.0)
                    b = props.get("B", 0.0)
                    n_val = props.get("N", 1.0)
                    c = props.get("C", 0.0)
                    f.write(f"\n/MAT/LAW44/{mid}\n")
                    f.write(f"{rho} {e} {nu}\n")
                    f.write(f"{a} {b} {n_val} {c}\n")
                else:
                    name = props.get("NAME", f"MAT_{mid}")
                    f.write(f"\n/MAT/LAW1/{mid}\n")
                    f.write(f"{name}\n")
                    f.write("#              RHO\n")
                    f.write(f"{rho}\n")
                    f.write("#                  E                  Nu\n")
                    f.write(f"{e} {nu}\n")

                if "FAIL" in props:
                    fail = props["FAIL"]
                    ftype = fail.get("TYPE", "").upper()
                    if ftype:
                        f.write(f"\n/{ftype}/{mid}\n")
                        vals = [str(v) for v in fail.values() if v != ftype]
                        if vals:
                            f.write(" ".join(vals) + "\n")
