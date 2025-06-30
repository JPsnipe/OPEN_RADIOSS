"""Create a basic Radioss starter file.

The block syntax follows the Radioss Input Reference Guide. Sections such
as ``/BCS`` for boundary conditions, ``/INTER`` for contact definitions and
``/IMPVEL`` for initial velocities are optional and can be enabled via
function parameters.
"""

from typing import Dict, List, Tuple, Any, TextIO
import math
import os

from .writer_inc import write_mesh_inc
from .material_defaults import apply_default_materials

DEFAULT_THICKNESS = 1.0
DEFAULT_E = 210000.0
DEFAULT_NU = 0.3
DEFAULT_RHO = 7800.0
DEFAULT_FINAL_TIME = 0.01
DEFAULT_ANIM_DT = 0.001
DEFAULT_HISTORY_DT = 1e-5
DEFAULT_DT_RATIO = 0.9
DEFAULT_RUNNAME = "model"

# Default engine control values derived from typical Radioss examples.
# See “/STOP” and “/PRINT” cards in the Altair Radioss 2022
# Reference Guide for recommended ranges.
DEFAULT_PRINT_N = -500
DEFAULT_PRINT_LINE = 55
DEFAULT_STOP_EMAX = 0.0
DEFAULT_STOP_MMAX = 0.0
DEFAULT_STOP_NMAX = 0.0
DEFAULT_STOP_NTH = 1
DEFAULT_STOP_NANIM = 1
DEFAULT_STOP_NERR = 0

# Additional output control defaults
DEFAULT_SHELL_ANIM_DT = None
DEFAULT_BRICK_ANIM_DT = None
DEFAULT_HISNODA_DT = None
DEFAULT_RFILE_DT = None

# Default Radioss version for the /VERS card and /BEGIN block
DEFAULT_RAD_VERSION = 2022


def _open_out(outfile: str | TextIO) -> tuple[TextIO, bool]:
    """Return a writable file object and whether it must be closed."""
    if hasattr(outfile, "write"):
        return outfile, False
    return open(outfile, "w"), True


def _merge_materials(
    base: Dict[int, Dict[str, float]] | None,
    extra: Dict[int, Dict[str, float]] | None,
) -> tuple[Dict[int, Dict[str, float]], Dict[int, int]]:
    """Merge two material dictionaries avoiding ID collisions.

    Returns a tuple ``(materials, id_map)`` where ``id_map`` provides the
    mapping from original material IDs to the final ones used in
    ``materials``. IDs present only in ``base`` will map to themselves.
    """

    result: Dict[int, Dict[str, float]] = {}
    id_map: Dict[int, int] = {}
    max_id = 0

    if base:
        result.update(base)
        max_id = max(base.keys(), default=0)
        for mid in base:
            id_map[mid] = mid

    if extra:
        for mid, props in extra.items():
            if mid in result:
                max_id += 1
                result[max_id] = props
                id_map[mid] = max_id
            else:
                result[mid] = props
                id_map[mid] = mid
                max_id = max(max_id, mid)

    return result, id_map



def _map_parts(
    parts: List[Dict[str, Any]] | None,
    mid_map: Dict[int, int],
    available: Dict[int, Dict[str, float]] | None,
) -> List[Dict[str, Any]]:
    """Return a new list of parts with material IDs updated.

    Raises ``ValueError`` if any part references a material ID not present
    in ``available`` after mapping. If ``available`` is ``None`` the check
    is skipped.
    """

    if not parts:
        return []

    mapped: List[Dict[str, Any]] = []
    for p in parts:
        p_copy = dict(p)
        mid_val = p_copy.get("mid")
        if mid_val is not None:
            try:
                old = int(mid_val)
            except (TypeError, ValueError):
                old = None
            if old is not None:
                new_id = mid_map.get(old, old)
                p_copy["mid"] = new_id
                if available is not None and new_id not in available:
                    name = p_copy.get("name", p_copy.get("id"))
                    raise ValueError(
                        f"Undefined material ID {old} for part {name}"
                    )
        mapped.append(p_copy)
    return mapped



def _write_interfaces(f, interfaces: List[Dict[str, object]] | None) -> None:
    """Write ``/INTER`` blocks to ``f`` if any interfaces are defined."""

    if not interfaces:
        return

    for idx, inter in enumerate(interfaces, start=1):
        itype = str(inter.get("type", "TYPE2")).upper()
        s_nodes = inter.get("slave", [])
        m_nodes = inter.get("master", [])
        name = inter.get("name", f"INTER_{idx}")
        fric = inter.get("fric", 0.0)
        fric_stiff = inter.get("stf")
        slave_id = 200 + idx
        master_id = 300 + idx

        if itype == "TYPE7":
            gap = inter.get("gap", 0.0)
            stiff = inter.get("stiff", 0.0)
            igap = inter.get("igap", 0)
            istf = inter.get("istf", 4)
            idel = inter.get("idel", 2)
            ibag = inter.get("ibag", 1)
            inacti = inter.get("inacti", 6)
            bumult = inter.get("bumult", 1.0)
            stfac = inter.get("stfac", 1.0)
            tstart = inter.get("tstart", 0.0)
            tstop = inter.get("tstop", 0.0)
            vis_s = inter.get("vis_s", 0.0)
            vis_f = inter.get("vis_f", 0.0)
            iform = inter.get("iform", 2)

            f.write(f"/INTER/TYPE7/{idx}\n")
            f.write(f"{name}\n")
            f.write(f"{slave_id} {master_id} {stiff} {gap} {igap}\n")
            f.write(f"{istf} {idel} {ibag} {inacti} {bumult}\n")
            f.write(f"{stfac}\n")
            f.write(f"{tstart} {tstop}\n")
            f.write(f"{vis_s} {vis_f}\n")
            f.write(f"{iform}\n")
        else:
            f.write(f"/INTER/TYPE2/{idx}\n")
            f.write(f"{name}\n")
            f.write(f"{slave_id} {master_id}\n")

        f.write(f"/GRNOD/NODE/{slave_id}\n")
        f.write(f"{name}_slave\n")
        for nid in s_nodes:
            f.write(f"{nid:10d}\n")

        f.write(f"/GRNOD/NODE/{master_id}\n")
        f.write(f"{name}_master\n")
        for nid in m_nodes:
            f.write(f"{nid:10d}\n")

        f.write("/FRICTION\n")
        if fric_stiff is None:
            f.write(f"{fric}\n")
        else:
            f.write(f"{fric} {fric_stiff}\n")


def _write_begin(f, runname: str, unit_sys: str | None) -> None:
    """Write the ``/BEGIN`` card with optional unit codes."""

    f.write("/BEGIN\n")
    f.write(f"{runname}\n")
    if unit_sys == "SI":
        f.write(f"      {DEFAULT_RAD_VERSION}         0\n")
        f.write("                  kg                  mm                  ms\n")
        f.write("                  kg                  mm                  ms\n")
    else:
        f.write(f"      {DEFAULT_RAD_VERSION}         0\n")
        f.write("                  1                  2                  3\n")
        f.write("                  1                  2                  3\n")

def write_starter(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str | TextIO,
    mesh_inc: str = "mesh.inc",
    include_inc: bool = True,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
    materials: Dict[int, Dict[str, float]] | None = None,
    extra_materials: Dict[int, Dict[str, float]] | None = None,
    *,
    thickness: float = DEFAULT_THICKNESS,
    young: float = DEFAULT_E,
    poisson: float = DEFAULT_NU,
    density: float = DEFAULT_RHO,
    runname: str = DEFAULT_RUNNAME,
    boundary_conditions: List[Dict[str, object]] | None = None,
    interfaces: List[Dict[str, object]] | None = None,
    rbody: List[Dict[str, object]] | None = None,
    rbe2: List[Dict[str, object]] | None = None,
    rbe3: List[Dict[str, object]] | None = None,
    init_velocity: Dict[str, object] | None = None,
    gravity: Dict[str, float] | None = None,
    properties: List[Dict[str, Any]] | None = None,
    parts: List[Dict[str, Any]] | None = None,
    subsets: Dict[str, List[int]] | None = None,
    auto_subsets: bool = True,
    default_material: bool = True,
    auto_properties: bool = True,
    auto_parts: bool = False,
    unit_sys: str | None = None,
    return_subset_map: bool = False,
) -> None | Tuple[None, Dict[str, int]]:
    """Write a Radioss starter file (``*_0000.rad``).

    ``unit_sys`` can be set to ``"SI"`` to output the ``/BEGIN`` card with
    kilogram--millimeter--millisecond units as used in legacy examples.
    Set ``auto_subsets=False`` to avoid generating ``/SUBSET`` cards
    from element groups referenced in ``parts``. ``auto_properties`` controls
    whether placeholder ``/PROP`` cards are inserted when no properties are
    provided but materials exist. ``auto_parts`` (``False`` by default) creates
    a default ``/PART`` only when set to ``True`` and no parts are supplied.
    Set ``return_subset_map=True`` to retrieve the mapping from subset names to
    the numeric IDs written in the file. The function then returns a tuple
    ``(None, subset_map)`` instead of ``None``.
    """

    all_mats, mid_map = _merge_materials(materials, extra_materials)
    if not all_mats and default_material:
        all_mats = {1: {}}
        mid_map = {1: 1}
    if all_mats:
        all_mats = apply_default_materials(all_mats)

    if all_mats:
        if auto_properties and not properties:
            from .utils import element_summary
            _, kw_counts = element_summary(elements)
            is_shell = kw_counts.get("SHELL", 0) >= kw_counts.get("BRICK", 0)
            if is_shell:
                properties = [
                    {
                        "id": 1,
                        "name": "AutoProp",
                        "type": "SHELL",
                        "thickness": thickness,
                    }
                ]
            else:
                properties = [
                    {
                        "id": 1,
                        "name": "AutoProp",
                        "type": "SOLID",
                        "Isolid": 24,
                    }
                ]

        if auto_parts and not parts and properties:
            mat_id = next(iter(all_mats.keys()), 1)
            parts = [
                {
                    "id": 1,
                    "name": "AutoPart",
                    "pid": properties[0]["id"],
                    "mid": mat_id,
                }
            ]

    if include_inc:
        write_mesh_inc(
            nodes,
            elements,
            mesh_inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
        )

    # Validate connector inputs
    if rbody:
        seen = set()
        for rb in rbody:
            rbid = rb.get("RBID")
            if rbid in seen:
                raise ValueError("Duplicate RBODY ID")
            seen.add(rbid)
            master = rb.get("Gnod_id")
            if master not in nodes:
                raise ValueError("RBODY master node missing")
            for nid in rb.get("nodes", []):
                if nid not in nodes:
                    raise ValueError("RBODY node not found")

    if rbe2:
        seen = set()
        for rb in rbe2:
            mid = rb.get("N_master")
            if mid not in nodes:
                raise ValueError("RBE2 master node missing")
            if mid in seen:
                raise ValueError("Duplicate RBE2 master")
            seen.add(mid)
            for nid in rb.get("N_slave_list", []):
                if nid not in nodes:
                    raise ValueError("RBE2 slave node missing")

    if rbe3:
        for rb in rbe3:
            dep = rb.get("N_dependent")
            if dep not in nodes:
                raise ValueError("RBE3 dependent node missing")
            for nid, _ in rb.get("independent", []):
                if nid not in nodes:
                    raise ValueError("RBE3 independent node missing")

    f, close_it = _open_out(outfile)
    try:
        f.write("#RADIOSS STARTER\n")
        _write_begin(f, runname, unit_sys)

        def write_law1(mid: int, name: str, rho: float, e: float, nu: float) -> None:
            f.write(f"/MAT/LAW1/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")

        def write_law2(mid: int, name: str, rho: float, e: float, nu: float, a: float, b: float, n_val: float, c_val: float, eps0: float) -> None:
            f.write(f"/MAT/LAW2/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#      A          B           n           C       EPS0\n")
            f.write(f"{a} {b} {n_val} {c_val} {eps0}\n")

        def write_law27(mid: int, name: str, rho: float, e: float, nu: float, sig0: float, su: float, epsu: float) -> None:
            f.write(f"/MAT/LAW27/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#    SIG0        SU       EPSU\n")
            f.write(f"{sig0} {su} {epsu}\n")

        def write_law36(mid: int, name: str, rho: float, e: float, nu: float, fs: float, fc: float, ch: float, curve: list[tuple[float, float]] | None) -> None:
            f.write(f"/MAT/LAW36/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("# fct_IDp  Fscale ...\n")
            fct_id = 100 + mid
            f.write(f"{fct_id} 1\n")
            f.write("#     Fs        Fc        Ch\n")
            f.write(f"{fs} {fc} {ch}\n")
            if curve:
                f.write(f"/FUNCT/{fct_id}\n")
                f.write(f"{name} curve\n")
                f.write("#     eps      \u03c3\n")
                for eps, sig in curve:
                    f.write(f"{eps} {sig}\n")

        def write_law44(mid: int, name: str, rho: float, e: float, nu: float, a: float, b: float, n_val: float, c_val: float) -> None:
            f.write(f"/MAT/LAW44/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#      A          B           n           C\n")
            f.write(f"{a} {b} {n_val} {c_val}\n")

        if not all_mats:
            if default_material:
                write_law1(1, "Default_Mat", density, young, poisson)
        else:
            for mid, props in all_mats.items():
                law = props.get("LAW", "LAW1").upper()
                name = props.get("NAME", f"MAT_{mid}")
                e = props.get("EX", young)
                nu = props.get("NUXY", poisson)
                rho = props.get("DENS", density)

                if law in ("LAW2", "JOHNSON_COOK", "PLAS_JOHNS"):
                    write_law2(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("A", 0.0),
                        props.get("B", 0.0),
                        props.get("N", 0.0),
                        props.get("C", 0.0),
                        props.get("EPS0", 1.0),
                    )
                elif law in ("LAW27", "PLAS_BRIT"):
                    write_law27(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("SIG0", 0.0),
                        props.get("SU", 0.0),
                        props.get("EPSU", 0.0),
                    )
                elif law in ("LAW36", "PLAS_TAB"):
                    curve = props.get("CURVE")
                    write_law36(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("Fsmooth", 0.0),
                        props.get("Fcut", 0.0),
                        props.get("Chard", 0.0),
                        curve if isinstance(curve, list) else None,
                    )
                elif law in ("LAW44", "COWPER"):
                    write_law44(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("A", 0.0),
                        props.get("B", 0.0),
                        props.get("N", 1.0),
                        props.get("C", 0.0),
                    )
                else:
                    write_law1(mid, name, rho, e, nu)

                if "FAIL" in props:
                    fail = props["FAIL"]
                    ftype = str(fail.get("TYPE", "")).upper()
                    if ftype == "JOHNSON":
                        d1 = fail.get("D1", -0.09)
                        d2 = fail.get("D2", 0.25)
                        d3 = fail.get("D3", -0.5)
                        d4 = fail.get("D4", 0.014)
                        d5 = fail.get("D5", 1.12)
                        eps0 = fail.get("EPS0", 1.0)
                        ifail_sh = fail.get("IFAIL_SH", 1)
                        ifail_so = fail.get("IFAIL_SO", 1)
                        dadv = fail.get("DADV", 0)
                        ixfem = fail.get("IXFEM", 0)
                        f.write(f"/FAIL/JOHNSON/{mid}\n")
                        f.write(f"{d1} {d2} {d3} {d4} {d5}\n")
                        f.write(f"{eps0} {ifail_sh} {ifail_so}\n")
                        f.write(f"{dadv}\n")
                        f.write(f"{ixfem}\n")
                    elif ftype == "BIQUAD":
                        alpha = fail.get("ALPHA", 0.0)
                        beta = fail.get("BETA", 0.0)
                        m = fail.get("M", 0.0)
                        n_fail = fail.get("N", 0.0)
                        f.write(f"/FAIL/BIQUAD/{mid}\n")
                        f.write("#    alpha      beta      m      n\n")
                        f.write(f"  {alpha}   {beta}   {m}   {n_fail}\n")
                    elif ftype:
                        f.write(f"/FAIL/{ftype}/{mid}\n")
                        vals = [str(v) for k, v in fail.items() if k not in {"TYPE", "NAME"}]
                        if vals:
                            f.write(" ".join(vals) + "\n")

        if include_inc:
            f.write(f"#include {mesh_inc}\n")

        if boundary_conditions:
            set_id_map = {
                n: i for i, n in enumerate(node_sets.keys(), start=1)
            } if node_sets else {}
            for idx, bc in enumerate(boundary_conditions, start=1):
                bc_type = str(bc.get("type", "BCS")).upper()
                name = bc.get("name", f"BC_{idx}")

                set_name = bc.get("set")
                use_existing_gid = False
                if set_name and set_name in set_id_map:
                    gid = set_id_map[set_name]
                    nodes_bc = node_sets.get(set_name, []) if node_sets else []
                    use_existing_gid = True
                else:
                    nodes_bc = bc.get("nodes", [])
                    gid = 100 + idx

                if bc_type == "BCS":
                    tra = str(bc.get("tra", "000")).rjust(3, "0")
                    rot = str(bc.get("rot", "000")).rjust(3, "0")
                    f.write(f"/BCS/{idx}\n")
                    f.write(f"{name}\n")
                    f.write("#  Trarot   Skew_ID  grnd_ID\n")
                    f.write(f"   {tra} {rot}         0        {gid}\n")
                elif bc_type == "PRESCRIBED_MOTION":
                    direction = int(bc.get("dir", 1))
                    value = float(bc.get("value", 0.0))
                    f.write(f"/BOUNDARY/PRESCRIBED_MOTION/{idx}\n")
                    f.write(f"{name}\n")
                    f.write("#   Dir    skew_ID   grnod_ID\n")
                    f.write(f"    {direction}        0        {gid}\n")
                    f.write(f"{value}\n")
                else:
                    f.write(f"# Unsupported BC type: {bc_type}\n")
                    continue

                if not use_existing_gid:
                    f.write(f"/GRNOD/NODE/{gid}\n")
                    f.write(f"{name}_nodes\n")
                    for nid in nodes_bc:
                        f.write(f"{nid:10d}\n")

        if interfaces:
            _write_interfaces(f, interfaces)

        if rbody:
            for idx, rb in enumerate(rbody, start=1):
                title = rb.get("title", "")
                f.write(f"/RBODY/{idx}\n")
                f.write(f"{title}\n")
                f.write("#     RBID  ISENS  NSKEW  ISPHER   MASS  Gnod_id  IKREM  ICOG  Surf_id\n")
                f.write(
                    f"     {rb.get('RBID',0)}     {rb.get('ISENS',0)}      {rb.get('NSKEW',0)}       {rb.get('ISPHER',0)}      {rb.get('MASS',0)}    {rb.get('Gnod_id',0)}     {rb.get('IKREM',0)}     {rb.get('ICOG',0)}       {rb.get('SURF_ID',0)}\n"
                )
                f.write("#     Jxx     Jyy     Jzz\n")
                f.write(
                    f"        {rb.get('Jxx',0)}       {rb.get('Jyy',0)}       {rb.get('Jzz',0)}\n"
                )
                f.write("#     Jxy     Jyz     Jxz\n")
                f.write(
                    f"        {rb.get('Jxy',0)}       {rb.get('Jyz',0)}       {rb.get('Jxz',0)}\n"
                )
                f.write("#     Ioptoff  Ifail\n")
                f.write(
                    f"     {rb.get('Ioptoff',0)}     {rb.get('Ifail',0)}\n"
                )

        if rbe2:
            for idx, rb in enumerate(rbe2, start=1):
                name = rb.get("name", f"RBE2_{idx}")
                f.write(f"/RBE2/{idx}\n")
                f.write(f"{name}\n")
                f.write("#  N_master   DOF_flags   MSELECT\n")
                f.write(
                    f"   {rb.get('N_master',0)}     {rb.get('DOF_flags','123456')}       {rb.get('MSELECT',1)}\n"
                )
                f.write("#  N_slave_list\n")
                slaves = rb.get('N_slave_list', [])
                if slaves:
                    f.write("   " + "   ".join(str(n) for n in slaves) + "\n")

        if rbe3:
            for idx, rb in enumerate(rbe3, start=1):
                name = rb.get("name", f"RBE3_{idx}")
                f.write(f"/RBE3/{idx}\n")
                f.write(f"{name}\n")
                f.write("#  N_dependent  DOF_flags   MSELECT\n")
                f.write(
                    f"   {rb.get('N_dependent',0)}        {rb.get('DOF_flags','123456')}        {rb.get('MSELECT',0)}\n"
                )
                f.write("#  N_indep  Weight\n")
                for nid, wt in rb.get('independent', []):
                    f.write(f"   {nid}     {wt}\n")

        subset_map: Dict[str, int] = {}
        all_subsets: Dict[str, List[int]] = dict(subsets or {})

        if parts:
            check_mats = None if not all_mats and default_material else all_mats
            mapped_parts = _map_parts(parts, mid_map, check_mats)

            if auto_subsets:
                used_sets = {p.get("set") for p in mapped_parts if p.get("set")}
                auto_subsets_dict = {
                    name: (elem_sets or {}).get(name, [])
                    for name in used_sets
                    if name not in all_subsets
                }
                all_subsets.update(auto_subsets_dict)

            # convert subset names to strings so numeric keys map correctly
            subset_map: Dict[str, int] = {
                str(n): i for i, n in enumerate(all_subsets.keys(), start=1)
            }

            for p in mapped_parts:
                pid = int(p.get("id", 1))
                name = p.get("name", f"PART_{pid}")
                prop_id = int(p.get("pid", 1))
                mat_id = int(p.get("mid", 1))
                set_name = p.get("set")
                subset_id = subset_map.get(str(set_name), 0) if set_name else 0

                f.write(f"/PART/{pid}\n")
                f.write(f"{name}\n")
                f.write(
                    f"         {prop_id}         {mat_id}         {subset_id}         \n"
                )

        if properties:
            for prop in properties:
                pid = int(prop.get("id", 1))
                pname = prop.get("name", f"PROP_{pid}")
                ptype = str(prop.get("type", "SHELL")).upper()
                if ptype == "SHELL":
                    thick = prop.get("thickness", thickness)
                    ishell = int(prop.get("Ishell", 24))
                    ismstr = int(prop.get("Ismstr", 0))
                    ish3n = int(prop.get("Ish3n", 0))
                    idrill = int(prop.get("Idrill", 0))
                    p_thick_fail = float(prop.get("P_thick_fail", 0))
                    hm = float(prop.get("hm", 0))
                    hf = float(prop.get("hf", 0))
                    hr = float(prop.get("hr", 0))
                    dm = float(prop.get("dm", 0))
                    dn = float(prop.get("dn", 0))
                    n = int(prop.get("N", 5))
                    istr = int(prop.get("Istrain", 0))
                    ashear = int(prop.get("Ashear", 0))
                    ithick = int(prop.get("Ithick", 1))
                    ip = int(prop.get("Iplas", 1))

                    f.write(f"/PROP/SHELL/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write("#   Ishell    Ismstr     Ish3n    Idrill              P_thick_fail\n")
                    f.write(f"        {ishell}         {ismstr}         {ish3n}        {idrill}                            {p_thick_fail}\n")
                    f.write("#                 hm                  hf            hr                  dm                  dn\n")
                    f.write(f"                   {hm}                   {hf}            {hr}                   {dm}                   {dn}\n")
                    f.write("#        N   Istrain               Thick   Ashear              Ithick     Iplas\n")
                    f.write(f"         {n}         {istr}                 {thick}                   {ashear}                   {ithick}         {ip}\n")
                elif ptype == "SOLID":
                    isol = int(prop.get("Isolid", 24))
                    ismstr = int(prop.get("Ismstr", 4))
                    icpre = int(prop.get("Icpre", 1))
                    itetra4 = int(prop.get("Itetra4", 0))
                    itetra10 = int(prop.get("Itetra10", 0))
                    imass = int(prop.get("Imass", 0))
                    iframe = int(prop.get("Iframe", 1))
                    ihkt = int(prop.get("IHKT", 0))
                    inpts = int(prop.get("Inpts", 0))
                    qa = float(prop.get("qa", 0.0))
                    qb = float(prop.get("qb", 0.0))
                    dn = float(prop.get("dn", 0.0))
                    h = float(prop.get("h", 0.0))
                    dtmin = float(prop.get("dtmin", 0.0))
                    ndir = int(prop.get("Ndir", 1))
                    sphpart = int(prop.get("sphpart_ID", 0))

                    f.write(f"/PROP/SOLID/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write(
                        "#  Isolid   Ismstr    Icpre   Itetra4   Itetra10   Imass   Iframe   IHKT\n"
                    )
                    f.write(
                        f"       {isol}        {ismstr}        {icpre}        {itetra4}        {itetra10}        {imass}        {iframe}        {ihkt}\n"
                    )
                    f.write("#   Inpts        qa         qb         dn          h\n")
                    f.write(
                        f"       {inpts}        {qa}        {qb}        {dn}        {h}\n"
                    )
                    f.write("#   dtmin      Ndir  sphpart_ID\n")
                    f.write(f"       {dtmin}        {ndir}        {sphpart}\n")
                else:
                    f.write(f"/PROP/{ptype}/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write("# property parameters not defined\n")

        if all_subsets:
            for idx, (name, ids) in enumerate(all_subsets.items(), start=1):
                f.write(f"/SUBSET/{idx}\n")
                f.write(f"{name}\n")
                line: List[str] = []
                for i, sid in enumerate(ids, 1):
                    line.append(str(sid))
                    if i % 10 == 0:
                        f.write(" ".join(line) + "\n")
                        line = []
                if line:
                    f.write(" ".join(line) + "\n")

        if init_velocity:
            nodes_v = init_velocity.get("nodes", [])
            vx = init_velocity.get("vx", 0.0)
            vy = init_velocity.get("vy", 0.0)
            vz = init_velocity.get("vz", 0.0)
            gid = 400
            f.write("/IMPVEL/1\n")
            f.write("0         X         0         0        400         0        0\n")
            f.write(f"{vx} {vy} {vz} 0\n")
            f.write(f"/GRNOD/NODE/{gid}\n")
            f.write("Init_Vel_Nodes\n")
            for nid in nodes_v:
                f.write(f"{nid:10d}\n")

        if gravity:
            g = float(gravity.get("g", 9.81))
            nx = float(gravity.get("nx", 0.0))
            ny = float(gravity.get("ny", 0.0))
            nz = float(gravity.get("nz", -1.0))
            comp = int(gravity.get("comp", 3))
            mag = math.sqrt(nx * nx + ny * ny + nz * nz)
            if mag:
                nx /= mag
                ny /= mag
                nz /= mag
            f.write("/GRAV\n")
            f.write(f"{comp} {g}\n")
            f.write(f"{nx} {ny} {nz}\n")

        f.write("/END\n")
    finally:
        if close_it:
            f.close()
        if isinstance(outfile, str):
            os.chmod(outfile, 0o644)
    if return_subset_map:
        return None, subset_map
    return None

    if return_subset_map:
        return None, subset_map
    return None
    if return_subset_map:
        return None, subset_map
    return None
    if return_subset_map:
        return None, subset_map
    return None

def write_engine(
    outfile: str | TextIO,
    *,
    runname: str = DEFAULT_RUNNAME,
    t_end: float = DEFAULT_FINAL_TIME,
    t_init: float = 0.0,
    anim_dt: float | None = DEFAULT_ANIM_DT,
    shell_anim_dt: float | None = DEFAULT_SHELL_ANIM_DT,
    brick_anim_dt: float | None = DEFAULT_BRICK_ANIM_DT,
    tfile_dt: float | None = DEFAULT_HISTORY_DT,
    hisnoda_dt: float | None = DEFAULT_HISNODA_DT,
    dt_ratio: float | None = DEFAULT_DT_RATIO,
    rfile_dt: float | None = DEFAULT_RFILE_DT,
    print_n: int | None = DEFAULT_PRINT_N,
    print_line: int | None = DEFAULT_PRINT_LINE,
    rfile_cycle: int | None = None,
    rfile_n: int | None = None,
    h3d_dt: float | None = None,
    stop_emax: float = DEFAULT_STOP_EMAX,
    stop_mmax: float = DEFAULT_STOP_MMAX,
    stop_nmax: float = DEFAULT_STOP_NMAX,
    stop_nth: int = DEFAULT_STOP_NTH,
    stop_nanim: int = DEFAULT_STOP_NANIM,
    stop_nerr: int = DEFAULT_STOP_NERR,
    out_ascii: bool = False,
    adyrel: Tuple[float | None, float | None] | None = None,
) -> None:
    """Write a Radioss engine file (``*_0001.rad``)."""

    f, close_it = _open_out(outfile)
    try:
        f.write("#RADIOSS ENGINE\n")
        if print_n is not None and print_line is not None:
            f.write(f"/PRINT/{print_n}/{print_line}\n")
        f.write(f"/RUN/{runname}/1\n")
        if t_init != 0.0:
            f.write(f"{t_init} {t_end}\n")
        else:
            f.write(f"                {t_end}\n")
        f.write("/STOP\n")
        f.write(f"{stop_emax} {stop_mmax} {stop_nmax} {stop_nth} {stop_nanim} {stop_nerr}\n")
        if tfile_dt is not None:
            f.write("/TFILE/0\n")
            f.write(f"{tfile_dt}\n")
        f.write(f"/VERS/{DEFAULT_RAD_VERSION}\n")
        if dt_ratio is not None:
            f.write("/DT/NODA/CST/0\n")
            f.write(f"{dt_ratio} 0 0\n")
        if anim_dt is not None:
            f.write("/ANIM/DT\n")
            f.write(f"0 {anim_dt}\n")
        if shell_anim_dt is not None:
            f.write("/ANIM/SHELL/DT\n")
            f.write(f"0 {shell_anim_dt}\n")
        if brick_anim_dt is not None:
            f.write("/ANIM/BRICK/DT\n")
            f.write(f"0 {brick_anim_dt}\n")
        if h3d_dt is not None:
            f.write("/H3D/DT\n")
            f.write(f"0 {h3d_dt}\n")
        if hisnoda_dt is not None:
            f.write("/HISNODA/DT\n")
            f.write(f"{hisnoda_dt}\n")
        if rfile_cycle is not None:
            if rfile_n is not None:
                f.write(f"/RFILE/{rfile_n}\n")
            else:
                f.write("/RFILE\n")
            f.write(f"{rfile_cycle}\n")
        if rfile_dt is not None:
            f.write("/RFILE/DT\n")
            f.write(f"{rfile_dt}\n")
        if out_ascii:
            f.write("/OUTP/ASCII\n")
        if adyrel is not None and (adyrel[0] is not None or adyrel[1] is not None):
            f.write("/ADYREL\n")
            tstart = 0.0 if adyrel[0] is None else adyrel[0]
            tstop = t_end if adyrel[1] is None else adyrel[1]
            f.write(f"{tstart} {tstop}\n")
    finally:
        if close_it:
            f.close()
        if isinstance(outfile, str):
            os.chmod(outfile, 0o644)
def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str | TextIO,
    mesh_inc: str = "mesh.inc",
    include_inc: bool = True,
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
    materials: Dict[int, Dict[str, float]] | None = None,
    extra_materials: Dict[int, Dict[str, float]] | None = None,
    *,
    thickness: float = DEFAULT_THICKNESS,
    young: float = DEFAULT_E,
    poisson: float = DEFAULT_NU,
    density: float = DEFAULT_RHO,

    runname: str = DEFAULT_RUNNAME,
    t_end: float = DEFAULT_FINAL_TIME,
    t_init: float = 0.0,
    anim_dt: float | None = DEFAULT_ANIM_DT,
    shell_anim_dt: float | None = DEFAULT_SHELL_ANIM_DT,
    brick_anim_dt: float | None = DEFAULT_BRICK_ANIM_DT,
    tfile_dt: float | None = DEFAULT_HISTORY_DT,
    hisnoda_dt: float | None = DEFAULT_HISNODA_DT,
    dt_ratio: float | None = DEFAULT_DT_RATIO,
    rfile_dt: float | None = DEFAULT_RFILE_DT,
    # Additional engine control options
    print_n: int | None = DEFAULT_PRINT_N,
    print_line: int | None = DEFAULT_PRINT_LINE,
    rfile_cycle: int | None = None,
    rfile_n: int | None = None,
    h3d_dt: float | None = None,
    stop_emax: float = DEFAULT_STOP_EMAX,
    stop_mmax: float = DEFAULT_STOP_MMAX,
    stop_nmax: float = DEFAULT_STOP_NMAX,
    stop_nth: int = DEFAULT_STOP_NTH,
    stop_nanim: int = DEFAULT_STOP_NANIM,
    stop_nerr: int = DEFAULT_STOP_NERR,
    out_ascii: bool = False,
    adyrel: Tuple[float | None, float | None] | None = None,
    boundary_conditions: List[Dict[str, object]] | None = None,
    interfaces: List[Dict[str, object]] | None = None,
    rbody: List[Dict[str, object]] | None = None,
    rbe2: List[Dict[str, object]] | None = None,
    rbe3: List[Dict[str, object]] | None = None,
    init_velocity: Dict[str, object] | None = None,
    gravity: Dict[str, float] | None = None,
    properties: List[Dict[str, Any]] | None = None,
    parts: List[Dict[str, Any]] | None = None,
    subsets: Dict[str, List[int]] | None = None,
    auto_subsets: bool = True,
    include_run: bool = True,
    default_material: bool = True,
    auto_properties: bool = True,
    auto_parts: bool = False,
    unit_sys: str | None = None,
    return_subset_map: bool = False,
) -> None | Tuple[None, Dict[str, int]]:
    """Generate ``model_0000.rad`` with optional solver controls.

    Parameters allow customizing material properties and basic engine
    settings such as final time, animation frequency and time-step
    controls. Pass ``None`` for ``anim_dt``, ``tfile_dt``, ``dt_ratio``,
    ``print_n`` or ``print_line`` to omit the corresponding block in
    the generated file. Gravity loading can be specified via the
    ``gravity`` parameter. Set ``include_inc`` to ``False`` to omit the
    ``#include`` line referencing the mesh. Use ``include_run=False`` to
    skip control cards like ``/RUN`` and ``/STOP``. Set ``default_material``
    to ``False`` to avoid inserting a placeholder material when none are
    provided. ``unit_sys`` behaves like the same argument in
    :func:`write_starter` and customizes the ``/BEGIN`` block. Use
    ``auto_subsets=False`` to skip the automatic creation of ``/SUBSET`` cards
    from element groups when ``parts`` reference them. ``auto_properties`` has
    the same meaning as in :func:`write_starter`. ``auto_parts`` (``False`` by
    default) inserts a placeholder ``/PART`` only when set to ``True`` and no
    parts are defined. Specify ``return_subset_map=True`` to get back a mapping
    from subset names to the numeric IDs used in the file; the return value will
    then be ``(None, subset_map)`` instead of ``None``.
    """

    all_mats, mid_map = _merge_materials(materials, extra_materials)
    if not all_mats and default_material:
        all_mats = {1: {}}
        mid_map = {1: 1}
    if all_mats:
        all_mats = apply_default_materials(all_mats)

    if all_mats:
        if auto_properties and not properties:
            from .utils import element_summary
            _, kw_counts = element_summary(elements)
            is_shell = kw_counts.get("SHELL", 0) >= kw_counts.get("BRICK", 0)
            if is_shell:
                properties = [
                    {
                        "id": 1,
                        "name": "AutoProp",
                        "type": "SHELL",
                        "thickness": thickness,
                    }
                ]
            else:
                properties = [
                    {
                        "id": 1,
                        "name": "AutoProp",
                        "type": "SOLID",
                        "Isolid": 24,
                    }
                ]

        if auto_parts and not parts and properties:
            mat_id = next(iter(all_mats.keys()), 1)
            parts = [
                {
                    "id": 1,
                    "name": "AutoPart",
                    "pid": properties[0]["id"],
                    "mid": mat_id,
                }
            ]

    if include_inc:
        write_mesh_inc(
            nodes,
            elements,
            mesh_inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
        )

    # Basic validation of connector definitions
    if rbody:
        seen = set()
        for rb in rbody:
            rbid = rb.get("RBID")
            if rbid in seen:
                raise ValueError("Duplicate RBODY ID")
            seen.add(rbid)
            master = rb.get("Gnod_id")
            if master not in nodes:
                raise ValueError("RBODY master node missing")
            for nid in rb.get("nodes", []):
                if nid not in nodes:
                    raise ValueError("RBODY node not found")

    if rbe2:
        seen = set()
        for rb in rbe2:
            mid = rb.get("N_master")
            if mid not in nodes:
                raise ValueError("RBE2 master node missing")
            if mid in seen:
                raise ValueError("Duplicate RBE2 master")
            seen.add(mid)
            for nid in rb.get("N_slave_list", []):
                if nid not in nodes:
                    raise ValueError("RBE2 slave node missing")

    if rbe3:
        for rb in rbe3:
            dep = rb.get("N_dependent")
            if dep not in nodes:
                raise ValueError("RBE3 dependent node missing")
            for nid, _ in rb.get("independent", []):
                if nid not in nodes:
                    raise ValueError("RBE3 independent node missing")

    f, close_it = _open_out(outfile)
    try:
        f.write("#RADIOSS STARTER\n")
        _write_begin(f, runname, unit_sys)

        if include_run:
            # General printout frequency
            if print_n is not None and print_line is not None:
                f.write(f"/PRINT/{print_n}/{print_line}\n")
            f.write(f"/RUN/{runname}/1\n")
            if t_init != 0.0:
                f.write(f"{t_init} {t_end}\n")
            else:
                f.write(f"                {t_end}\n")
            f.write("/STOP\n")
            f.write(
                f"{stop_emax} {stop_mmax} {stop_nmax} {stop_nth} {stop_nanim} {stop_nerr}\n"
            )
            if tfile_dt is not None:
                f.write("/TFILE/0\n")
                f.write(f"{tfile_dt}\n")
            f.write(f"/VERS/{DEFAULT_RAD_VERSION}\n")
            if dt_ratio is not None:
                f.write("/DT/NODA/CST/0\n")
                f.write(f"{dt_ratio} 0 0\n")
            if anim_dt is not None:
                f.write("/ANIM/DT\n")
                f.write(f"0 {anim_dt}\n")
            if shell_anim_dt is not None:
                f.write("/ANIM/SHELL/DT\n")
                f.write(f"0 {shell_anim_dt}\n")
            if brick_anim_dt is not None:
                f.write("/ANIM/BRICK/DT\n")
                f.write(f"0 {brick_anim_dt}\n")
            if h3d_dt is not None:
                f.write("/H3D/DT\n")
                f.write(f"0 {h3d_dt}\n")
            if hisnoda_dt is not None:
                f.write("/HISNODA/DT\n")
                f.write(f"{hisnoda_dt}\n")
            if rfile_cycle is not None:
                if rfile_n is not None:
                    f.write(f"/RFILE/{rfile_n}\n")
                else:
                    f.write("/RFILE\n")
                f.write(f"{rfile_cycle}\n")
            if rfile_dt is not None:
                f.write("/RFILE/DT\n")
                f.write(f"{rfile_dt}\n")
            if out_ascii:
                f.write("/OUTP/ASCII\n")
            if adyrel is not None and (adyrel[0] is not None or adyrel[1] is not None):
                f.write("/ADYREL\n")
                tstart = 0.0 if adyrel[0] is None else adyrel[0]
                tstop = t_end if adyrel[1] is None else adyrel[1]
                f.write(f"{tstart} {tstop}\n")

        # 2. MATERIALS
        def write_law1(mid: int, name: str, rho: float, e: float, nu: float) -> None:
            f.write(f"/MAT/LAW1/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")

        def write_law2(mid: int, name: str, rho: float, e: float, nu: float, a: float, b: float, n_val: float, c_val: float, eps0: float) -> None:
            f.write(f"/MAT/LAW2/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#      A          B           n           C       EPS0\n")
            f.write(f"{a} {b} {n_val} {c_val} {eps0}\n")

        def write_law27(mid: int, name: str, rho: float, e: float, nu: float, sig0: float, su: float, epsu: float) -> None:
            f.write(f"/MAT/LAW27/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#    SIG0        SU       EPSU\n")
            f.write(f"{sig0} {su} {epsu}\n")

        def write_law36(mid: int, name: str, rho: float, e: float, nu: float, fs: float, fc: float, ch: float, curve: list[tuple[float, float]] | None) -> None:
            f.write(f"/MAT/LAW36/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("# fct_IDp  Fscale ...\n")
            fct_id = 100 + mid
            f.write(f"{fct_id} 1\n")
            f.write("#     Fs        Fc        Ch\n")
            f.write(f"{fs} {fc} {ch}\n")
            if curve:
                f.write(f"/FUNCT/{fct_id}\n")
                f.write(f"{name} curve\n")
                f.write("#     eps      \u03c3\n")
                for eps, sig in curve:
                    f.write(f"{eps} {sig}\n")

        def write_law44(mid: int, name: str, rho: float, e: float, nu: float, a: float, b: float, n_val: float, c_val: float) -> None:
            f.write(f"/MAT/LAW44/{mid}\n")
            f.write(f"{name}\n")
            f.write("#              RHO\n")
            f.write(f"{rho}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{e} {nu}\n")
            f.write("#      A          B           n           C\n")
            f.write(f"{a} {b} {n_val} {c_val}\n")

        if not all_mats:
            if default_material:
                write_law1(1, "Default_Mat", density, young, poisson)
        else:
            for mid, props in all_mats.items():
                law = props.get("LAW", "LAW1").upper()
                name = props.get("NAME", f"MAT_{mid}")
                e = props.get("EX", young)
                nu = props.get("NUXY", poisson)
                rho = props.get("DENS", density)

                if law in ("LAW2", "JOHNSON_COOK", "PLAS_JOHNS"):
                    write_law2(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("A", 0.0),
                        props.get("B", 0.0),
                        props.get("N", 0.0),
                        props.get("C", 0.0),
                        props.get("EPS0", 1.0),
                    )
                elif law in ("LAW27", "PLAS_BRIT"):
                    write_law27(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("SIG0", 0.0),
                        props.get("SU", 0.0),
                        props.get("EPSU", 0.0),
                    )
                elif law in ("LAW36", "PLAS_TAB"):
                    curve = props.get("CURVE")
                    write_law36(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("Fsmooth", 0.0),
                        props.get("Fcut", 0.0),
                        props.get("Chard", 0.0),
                        curve if isinstance(curve, list) else None,
                    )
                elif law in ("LAW44", "COWPER"):
                    write_law44(
                        mid,
                        name,
                        rho,
                        e,
                        nu,
                        props.get("A", 0.0),
                        props.get("B", 0.0),
                        props.get("N", 1.0),
                        props.get("C", 0.0),
                    )
                else:
                    write_law1(mid, name, rho, e, nu)

                if "FAIL" in props:
                    fail = props["FAIL"]
                    ftype = str(fail.get("TYPE", "")).upper()
                    if ftype == "JOHNSON":
                        d1 = fail.get("D1", -0.09)
                        d2 = fail.get("D2", 0.25)
                        d3 = fail.get("D3", -0.5)
                        d4 = fail.get("D4", 0.014)
                        d5 = fail.get("D5", 1.12)
                        eps0 = fail.get("EPS0", 1.0)
                        ifail_sh = fail.get("IFAIL_SH", 1)
                        ifail_so = fail.get("IFAIL_SO", 1)
                        dadv = fail.get("DADV", 0)
                        ixfem = fail.get("IXFEM", 0)
                        f.write(f"/FAIL/JOHNSON/{mid}\n")
                        f.write(f"{d1} {d2} {d3} {d4} {d5}\n")
                        f.write(f"{eps0} {ifail_sh} {ifail_so}\n")
                        f.write(f"{dadv}\n")
                        f.write(f"{ixfem}\n")
                    elif ftype == "BIQUAD":
                        alpha = fail.get("ALPHA", 0.0)
                        beta = fail.get("BETA", 0.0)
                        m = fail.get("M", 0.0)
                        n_fail = fail.get("N", 0.0)
                        f.write(f"/FAIL/BIQUAD/{mid}\n")
                        f.write("#    alpha      beta      m      n\n")
                        f.write(f"  {alpha}   {beta}   {m}   {n_fail}\n")
                    elif ftype:
                        f.write(f"/FAIL/{ftype}/{mid}\n")
                        fname = fail.get("NAME")
                        if fname:
                            f.write(f"{fname}\n")
                        vals = [
                            str(v)
                            for k, v in fail.items()
                            if k not in {"TYPE", "NAME"}
                        ]
                        if vals:
                            f.write(" ".join(vals) + "\n")

        # 3. NODES (from include file)
        if include_inc:
            f.write(f"#include {mesh_inc}\n")


        # 4. BOUNDARY CONDITIONS

        if boundary_conditions:
            set_id_map = {
                n: i for i, n in enumerate(node_sets.keys(), start=1)
            } if node_sets else {}
            for idx, bc in enumerate(boundary_conditions, start=1):
                bc_type = str(bc.get("type", "BCS")).upper()
                name = bc.get("name", f"BC_{idx}")

                set_name = bc.get("set")
                use_existing_gid = False
                if set_name and set_name in set_id_map:
                    gid = set_id_map[set_name]
                    nodes_bc = node_sets.get(set_name, []) if node_sets else []
                    use_existing_gid = True
                else:
                    nodes_bc = bc.get("nodes", [])
                    gid = 100 + idx

                if bc_type == "BCS":
                    tra = str(bc.get("tra", "000")).rjust(3, "0")
                    rot = str(bc.get("rot", "000")).rjust(3, "0")
                    f.write(f"/BCS/{idx}\n")
                    f.write(f"{name}\n")
                    f.write("#  Trarot   Skew_ID  grnd_ID\n")
                    f.write(f"   {tra} {rot}         0        {gid}\n")
                elif bc_type == "PRESCRIBED_MOTION":
                    direction = int(bc.get("dir", 1))
                    value = float(bc.get("value", 0.0))
                    f.write(f"/BOUNDARY/PRESCRIBED_MOTION/{idx}\n")
                    f.write(f"{name}\n")
                    f.write("#   Dir    skew_ID   grnod_ID\n")
                    f.write(f"    {direction}        0        {gid}\n")
                    f.write(f"{value}\n")
                else:
                    f.write(f"# Unsupported BC type: {bc_type}\n")
                    continue

                if not use_existing_gid:
                    f.write(f"/GRNOD/NODE/{gid}\n")
                    f.write(f"{name}_nodes\n")
                    for nid in nodes_bc:
                        f.write(f"{nid:10d}\n")

        if interfaces:
            _write_interfaces(f, interfaces)

        # 5. RIGID CONNECTORS

        if rbody:
            for idx, rb in enumerate(rbody, start=1):
                title = rb.get("title", "")
                f.write(f"/RBODY/{idx}\n")
                f.write(f"{title}\n")
                f.write("#     RBID  ISENS  NSKEW  ISPHER   MASS  Gnod_id  IKREM  ICOG  Surf_id\n")
                f.write(
                    f"     {rb.get('RBID',0)}     {rb.get('ISENS',0)}      {rb.get('NSKEW',0)}       {rb.get('ISPHER',0)}      {rb.get('MASS',0)}    {rb.get('Gnod_id',0)}     {rb.get('IKREM',0)}     {rb.get('ICOG',0)}       {rb.get('SURF_ID',0)}\n"
                )
                f.write("#     Jxx     Jyy     Jzz\n")
                f.write(
                    f"        {rb.get('Jxx',0)}       {rb.get('Jyy',0)}       {rb.get('Jzz',0)}\n"
                )
                f.write("#     Jxy     Jyz     Jxz\n")
                f.write(
                    f"        {rb.get('Jxy',0)}       {rb.get('Jyz',0)}       {rb.get('Jxz',0)}\n"
                )
                f.write("#     Ioptoff  Ifail\n")
                f.write(
                    f"     {rb.get('Ioptoff',0)}     {rb.get('Ifail',0)}\n"
                )

        if rbe2:
            for idx, rb in enumerate(rbe2, start=1):
                name = rb.get("name", f"RBE2_{idx}")
                f.write(f"/RBE2/{idx}\n")
                f.write(f"{name}\n")
                f.write("#  N_master   DOF_flags   MSELECT\n")
                f.write(
                    f"   {rb.get('N_master',0)}     {rb.get('DOF_flags','123456')}       {rb.get('MSELECT',1)}\n"
                )
                f.write("#  N_slave_list\n")
                slaves = rb.get('N_slave_list', [])
                if slaves:
                    f.write("   " + "   ".join(str(n) for n in slaves) + "\n")

        if rbe3:
            for idx, rb in enumerate(rbe3, start=1):
                name = rb.get("name", f"RBE3_{idx}")
                f.write(f"/RBE3/{idx}\n")
                f.write(f"{name}\n")
                f.write("#  N_dependent  DOF_flags   MSELECT\n")
                f.write(
                    f"   {rb.get('N_dependent',0)}        {rb.get('DOF_flags','123456')}        {rb.get('MSELECT',0)}\n"
                )
                f.write("#  N_indep  Weight\n")
                for nid, wt in rb.get('independent', []):
                    f.write(f"   {nid}     {wt}\n")

        # 6. PARTS AND PROPERTIES

        subset_map: Dict[str, int] = {}
        all_subsets: Dict[str, List[int]] = dict(subsets or {})

        if parts:
            check_mats = None if not all_mats and default_material else all_mats
            mapped_parts = _map_parts(parts, mid_map, check_mats)

            if auto_subsets:
                used_sets = {p.get("set") for p in mapped_parts if p.get("set")}
                auto_subsets_dict = {
                    name: (elem_sets or {}).get(name, [])
                    for name in used_sets
                    if name not in all_subsets
                }
                all_subsets.update(auto_subsets_dict)
            # convert subset names to strings so numeric keys map correctly

            subset_map: Dict[str, int] = {
                str(n): i for i, n in enumerate(all_subsets.keys(), start=1)
            }

            for p in mapped_parts:
                pid = int(p.get("id", 1))
                name = p.get("name", f"PART_{pid}")
                prop_id = int(p.get("pid", 1))
                mat_id = int(p.get("mid", 1))
                set_name = p.get("set")
                subset_id = subset_map.get(str(set_name), 0) if set_name else 0
                f.write(f"/PART/{pid}\n")
                f.write(f"{name}\n")
                f.write(
                    f"         {prop_id}         {mat_id}         {subset_id}         \n"
                )

        if properties:
            for prop in properties:
                pid = int(prop.get("id", 1))
                pname = prop.get("name", f"PROP_{pid}")
                ptype = str(prop.get("type", "SHELL")).upper()
                if ptype == "SHELL":
                    thick = prop.get("thickness", thickness)
                    ishell = int(prop.get("Ishell", 24))
                    ismstr = int(prop.get("Ismstr", 0))
                    ish3n = int(prop.get("Ish3n", 0))
                    idrill = int(prop.get("Idrill", 0))
                    p_thick_fail = float(prop.get("P_thick_fail", 0))
                    hm = float(prop.get("hm", 0))
                    hf = float(prop.get("hf", 0))
                    hr = float(prop.get("hr", 0))
                    dm = float(prop.get("dm", 0))
                    dn = float(prop.get("dn", 0))
                    n = int(prop.get("N", 5))
                    istr = int(prop.get("Istrain", 0))
                    ashear = int(prop.get("Ashear", 0))
                    ithick = int(prop.get("Ithick", 1))
                    ip = int(prop.get("Iplas", 1))

                    f.write(f"/PROP/SHELL/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write("#   Ishell    Ismstr     Ish3n    Idrill                         P_thick_fail\n")
                    f.write(f"        {ishell}         {ismstr}         {ish3n}         {idrill}                            {p_thick_fail}\n")
                    f.write("#                 hm                  hf               hr                  dm                  dn\n")
                    f.write(f"                   {hm}                   {hf}                {hr}                   {dm}                   {dn}\n")
                    f.write("#        N   Istrain               Thick           Ashear              Ithick     Iplas\n")
                    f.write(f"         {n}         {istr}                 {thick}                   {ashear}                   {ithick}         {ip}\n")
                elif ptype == "SOLID":
                    isol = int(prop.get("Isolid", 24))
                    ismstr = int(prop.get("Ismstr", 4))
                    icpre = int(prop.get("Icpre", 1))
                    iframe = int(prop.get("Iframe", 1))
                    inpts = prop.get("Inpts")
                    qa = prop.get("qa")
                    qb = prop.get("qb")
                    dn = prop.get("dn")
                    h = prop.get("h")

                    f.write(f"/PROP/SOLID/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write("#  Isolid   Ismstr    Icpre   Iframe\n")
                    f.write(
                        f"       {isol}        {ismstr}        {icpre}        {iframe}\n"
                    )
                    headers = []
                    values = []
                    if inpts is not None:
                        headers.append("Inpts")
                        values.append(f"{int(inpts):5d}")
                    if qa is not None:
                        headers.append("qa")
                        values.append(f"{float(qa):<8g}")
                    if qb is not None:
                        headers.append("qb")
                        values.append(f"{float(qb):<8g}")
                    if dn is not None:
                        headers.append("dn")
                        values.append(f"{float(dn):<8g}")
                    if h is not None and float(h) != 0.0:
                        headers.append("h")
                        values.append(f"{float(h):<8g}")
                    if headers:
                        f.write("#  " + "        ".join(headers) + "\n")
                        f.write("   " + "   ".join(values) + "\n")
                else:
                    f.write(f"/PROP/{ptype}/{pid}\n")
                    f.write(f"{pname}\n")
                    f.write("# property parameters not defined\n")

        if all_subsets:
            for idx, (name, ids) in enumerate(all_subsets.items(), start=1):
                f.write(f"/SUBSET/{idx}\n")
                f.write(f"{name}\n")
                line: List[str] = []
                for i, sid in enumerate(ids, 1):
                    line.append(str(sid))
                    if i % 10 == 0:
                        f.write(" ".join(line) + "\n")
                        line = []
                if line:
                    f.write(" ".join(line) + "\n")

        if init_velocity:
            nodes_v = init_velocity.get("nodes", [])
            vx = init_velocity.get("vx", 0.0)
            vy = init_velocity.get("vy", 0.0)
            vz = init_velocity.get("vz", 0.0)
            gid = 400
            f.write("/IMPVEL/1\n")
            f.write("0         X         0         0        400         0         0\n")
            f.write(f"{vx} {vy} {vz} 0\n")
            f.write(f"/GRNOD/NODE/{gid}\n")
            f.write("Init_Vel_Nodes\n")
            for nid in nodes_v:
                f.write(f"{nid:10d}\n")

        if gravity:
            g = float(gravity.get("g", 9.81))
            nx = float(gravity.get("nx", 0.0))
            ny = float(gravity.get("ny", 0.0))
            nz = float(gravity.get("nz", -1.0))
            comp = int(gravity.get("comp", 3))
            mag = math.sqrt(nx * nx + ny * ny + nz * nz)
            if mag:
                nx /= mag
                ny /= mag
                nz /= mag
            f.write("/GRAV\n")
            f.write(f"{comp} {g}\n")
            f.write(f"{nx} {ny} {nz}\n")

        f.write("/END\n")
    finally:
        if close_it:
            f.close()
        if isinstance(outfile, str):
            os.chmod(outfile, 0o644)

    if return_subset_map:
        return None, subset_map
    return None
