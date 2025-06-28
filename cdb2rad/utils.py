"""Utility helpers for analyzing elements."""

from typing import List, Tuple, Dict
import json
from pathlib import Path

# Basic mapping from Ansys ``ETYP`` numbers to element names.  The list is not
# exhaustive but covers the values present in the example ``model.cdb`` and
# common cases.  Unknown numbers fall back to ``ETYP{num}``.
ETYP_NAMES: Dict[int, str] = {
    1: "SOLID185",
    2: "SHELL181",
    4: "SHELL63",
    45: "SHELL45",
    181: "SHELL181",
    182: "SHELL281",
    185: "SOLID185",
    186: "SOLID186",
    187: "SOLID187",
}


def element_summary(
    elements: List[Tuple[int, int, List[int]]],
    mapping_file: str | None = None,
) -> tuple[Dict[int, int], Dict[str, int]]:
    """Return counts by Ansys ``etype`` and Radioss keyword.

    Parameters
    ----------
    elements : list of tuples
        Sequence ``(eid, etype, node_ids)`` from :func:`parse_cdb`.
    mapping_file : str, optional
        Path to ``mapping.json``. When ``None`` uses the file next to this
        module.

    Returns
    -------
    tuple
        ``(etype_counts, keyword_counts)`` dictionaries.
    """
    if mapping_file is None:
        mapping_path = Path(__file__).with_name("mapping.json")
    else:
        mapping_path = Path(mapping_file)

    with open(mapping_path, "r", encoding="utf-8") as mf:
        mapping: Dict[str, str] = json.load(mf)

    etype_counts: Dict[int, int] = {}
    keyword_counts: Dict[str, int] = {}
    for _eid, etype, nids in elements:
        etype_counts[etype] = etype_counts.get(etype, 0) + 1
        key = mapping.get(str(etype))
        if not key:
            if len(nids) in (4, 3):
                key = "SHELL"
            elif len(nids) in (8, 20):
                key = "BRICK"
            elif len(nids) in (4, 10):
                key = "TETRA"
            else:
                key = "UNKNOWN"
        keyword_counts[key] = keyword_counts.get(key, 0) + 1

    return etype_counts, keyword_counts


def element_set_types(
    elements: List[Tuple[int, int, List[int]]],
    elem_sets: Dict[str, List[int]],
    mapping_file: str | None = None,
) -> Dict[str, Dict[str, int]]:
    """Return Radioss keyword counts for each element set.

    Parameters
    ----------
    elements : list of tuples
        Sequence ``(eid, etype, node_ids)`` from :func:`parse_cdb`.
    elem_sets : dict
        Mapping ``{name: [elem_ids]}`` from :func:`parse_cdb`.
    mapping_file : str, optional
        Path to ``mapping.json``. When ``None`` uses the file next to this
        module.

    Returns
    -------
    dict
        ``{set_name: {keyword: count}}`` mapping.
    """

    if mapping_file is None:
        mapping_path = Path(__file__).with_name("mapping.json")
    else:
        mapping_path = Path(mapping_file)

    with open(mapping_path, "r", encoding="utf-8") as mf:
        mapping: Dict[str, str] = json.load(mf)

    eid_map: Dict[int, tuple[int, int]] = {
        eid: (etype, len(nids)) for eid, etype, nids in elements
    }

    result: Dict[str, Dict[str, int]] = {}
    for name, ids in elem_sets.items():
        counts: Dict[str, int] = {}
        for eid in ids:
            info = eid_map.get(eid)
            if not info:
                continue
            etype, n = info
            key = mapping.get(str(etype))
            if not key:
                if n in (4, 3):
                    key = "SHELL"
                elif n in (8, 20):
                    key = "BRICK"
                elif n in (4, 10):
                    key = "TETRA"
                else:
                    key = "UNKNOWN"
            counts[key] = counts.get(key, 0) + 1
        result[name] = counts

    return result



def element_set_etypes(
    elements: List[Tuple[int, int, List[int]]],
    elem_sets: Dict[str, List[int]],
    name_map: Dict[int, str] | None = None,
) -> Dict[str, Dict[str, int]]:
    """Return Ansys ETYP name counts for each element set."""

    if name_map is None:
        name_map = ETYP_NAMES

    eid_map: Dict[int, int] = {eid: etype for eid, etype, _ in elements}

    result: Dict[str, Dict[str, int]] = {}
    for set_name, ids in elem_sets.items():
        counts: Dict[str, int] = {}
        for eid in ids:
            etype = eid_map.get(eid)
            if etype is None:
                continue
            aname = name_map.get(etype, f"ETYP{etype}")
            counts[aname] = counts.get(aname, 0) + 1
        result[set_name] = counts

    return result



def check_rad_inputs(
    use_cdb_mats: bool,
    materials: Dict[int, Dict[str, float]] | None,
    use_impact: bool,
    impact_materials: List[Dict[str, float]] | None,
    bcs: List[Dict[str, object]] | None,
    interfaces: List[Dict[str, object]] | None,
    properties: List[Dict[str, object]] | None = None,
    parts: List[Dict[str, object]] | None = None,
    subsets: Dict[str, List[int]] | None = None,
    node_sets: Dict[str, List[int]] | None = None,
    nodes: Dict[int, List[float]] | None = None,
    advanced: bool = False,
) -> List[tuple[bool, str]]:
    """Return a list of ``(status, message)`` tuples summarising the checks."""

    results: List[tuple[bool, str]] = []

    # 1. Materials
    n_mats = 0
    if use_cdb_mats and materials:
        n_mats += len(materials)
    if use_impact and impact_materials:
        n_mats += len(impact_materials)
    ok = n_mats > 0
    results.append((ok, f"Materiales definidos: {n_mats}"))

    # 2. Properties
    n_props = len(properties or [])
    results.append((n_props > 0, f"Propiedades definidas: {n_props}"))

    # 3. Parts
    n_parts = len(parts or [])
    results.append((n_parts > 0, f"Partes definidas: {n_parts}"))

    mat_ids = set()
    if materials:
        mat_ids.update(int(m) for m in materials.keys())
    if impact_materials:
        for m in impact_materials:
            if "id" in m:
                try:
                    mat_ids.add(int(m["id"]))
                except (TypeError, ValueError):
                    pass
    prop_ids = {int(p.get("id", 0)) for p in properties or []}

    # 4. Part references
    if parts:
        for pt in parts:
            pid = int(pt.get("pid", 0))
            mid = int(pt.get("mid", 0))
            if pid not in prop_ids:
                results.append((False, f"PART {pt.get('id')} referencia PROP {pid} inexistente"))
                break
            if mid not in mat_ids:
                results.append((False, f"PART {pt.get('id')} referencia MAT {mid} inexistente"))
                break

    # 5. Subset usage
    if subsets:
        used = {pt.get("set") for pt in parts or [] if pt.get("set")}
        unused = [name for name in subsets.keys() if name not in used]
        for sub in unused:
            results.append((False, f"Subset sin uso: {sub}"))

    # 6. Node set existence
    if bcs and node_sets and nodes:
        node_ids = set(nodes.keys())
        for idx, bc in enumerate(bcs, start=1):
            undefined = [n for n in bc.get("nodes", []) if n not in node_ids]
            if undefined:
                nid = undefined[0]
                results.append((False, f"Nodo no definido en BC {idx}: {nid}"))
                break

    # 7. Interface completeness
    if interfaces:
        for idx, itf in enumerate(interfaces, start=1):
            if not itf.get("slave") or not itf.get("master"):
                results.append((False, f"Interfaz {idx} incompleta"))
                break

    # 8. Advanced checks
    if advanced and properties:
        for p in properties:
            if p.get("type") == "SHELL":
                pid = p.get("id")
                if float(p.get("thickness", 0.0)) <= 0.0:
                    results.append((False, f"Espesor en PROP/SHELL/{pid} = 0.0"))
                ishell = int(p.get("Ishell", 24))
                valid_ishell = {1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 23, 24}
                if ishell not in valid_ishell:
                    results.append((False, f"Ishell no valido en PROP/SHELL/{pid}"))
                    continue
                if any(float(p.get(k, 0.0)) != 0.0 for k in ("hm", "hf", "hr", "dm", "dn")) and ishell != 24:
                    results.append((True, f"WARNING: Parametros de hora solo validos con Ishell 24 en PROP/SHELL/{pid}"))
                    continue
            if p.get("type") == "SOLID":
                pid = p.get("id")
                isolid = int(p.get("Isolid", 24))
                if isolid not in {0, 1, 2, 5, 14, 16, 17, 18, 24}:
                    results.append((True, f"WARNING: Isolid no valido en PROP/SOLID/{pid}"))
                    continue
                if int(p.get("Icpre", 0)) and isolid not in {14, 17, 18, 24}:
                    results.append((True, f"WARNING: Icpre incompatible con Isolid en PROP/SOLID/{pid}"))
                    continue
                if p.get("Inpts") is not None and isolid not in {14, 16}:
                    results.append((True, f"WARNING: Inpts solo valido con Isolid 14 o 16 en PROP/SOLID/{pid}"))
                    continue
                if float(p.get("dn", 0.0)) != 0.0 and isolid != 24:
                    results.append((True, f"WARNING: dn solo valido con Isolid 24 en PROP/SOLID/{pid}"))
                    continue
                if float(p.get("h", 0.0)) != 0.0 and isolid not in {1, 2}:
                    results.append((True, f"WARNING: h solo valido con Isolid 1 o 2 en PROP/SOLID/{pid}"))
                    continue
                iframe = int(p.get("Iframe", 1))
                if isolid in {14, 24} and iframe != 2:
                    results.append((True, f"WARNING: Iframe debe ser 2 para Isolid {isolid} en PROP/SOLID/{pid}"))
                    continue

    return results
