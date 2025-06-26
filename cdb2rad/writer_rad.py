"""Create a basic Radioss starter file.

The block syntax follows the Radioss Input Reference Guide. Sections such
as ``/BCS`` for boundary conditions, ``/INTER`` for contact definitions and
``/IMPVEL`` for initial velocities are optional and can be enabled via
function parameters.
"""

from typing import Dict, List, Tuple

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


def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
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
    anim_dt: float = DEFAULT_ANIM_DT,
    tfile_dt: float = DEFAULT_HISTORY_DT,
    dt_ratio: float = DEFAULT_DT_RATIO,
    # Additional engine control options
    print_n: int = DEFAULT_PRINT_N,
    print_line: int = DEFAULT_PRINT_LINE,
    rfile_cycle: int | None = None,
    rfile_n: int | None = None,
    h3d_dt: float | None = None,
    stop_emax: float = DEFAULT_STOP_EMAX,
    stop_mmax: float = DEFAULT_STOP_MMAX,
    stop_nmax: float = DEFAULT_STOP_NMAX,
    stop_nth: int = DEFAULT_STOP_NTH,
    stop_nanim: int = DEFAULT_STOP_NANIM,
    stop_nerr: int = DEFAULT_STOP_NERR,
    adyrel: Tuple[float | None, float | None] | None = None,
    boundary_conditions: List[Dict[str, object]] | None = None,
    interfaces: List[Dict[str, object]] | None = None,
    init_velocity: Dict[str, object] | None = None,
    gravity: Dict[str, float] | None = None,

) -> None:
    """Generate ``model_0000.rad`` with optional solver controls.

    Parameters allow customizing material properties and basic engine
    settings such as final time, animation frequency and time-step
    controls. Gravity loading can be specified via the ``gravity``
    parameter. Set ``include_inc`` to ``False`` to omit the
    ``#include`` line referencing the mesh.
    """

    all_mats: Dict[int, Dict[str, float]] = {}
    if materials:
        all_mats.update(materials)
    if extra_materials:
        all_mats.update(extra_materials)
    if all_mats:
        all_mats = apply_default_materials(all_mats)

    if include_inc:
        write_mesh_inc(
            nodes,
            elements,
            mesh_inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=all_mats if all_mats else None,
        )

    with open(outfile, "w") as f:
        f.write("#RADIOSS STARTER\n")
        f.write("/BEGIN\n")
        f.write(f"{runname}\n")
        f.write("     2024         0\n")
        f.write("                  kg                  mm                   s\n")
        f.write("                  kg                  mm                   s\n")

        # 1. CONTROL CARDS
        # General printout frequency
        f.write(f"/PRINT/{print_n}/{print_line}\n")
        f.write(f"/RUN/{runname}/1/\n")
        f.write(f"                {t_end}\n")
        f.write("/STOP\n")
        f.write(
            f"{stop_emax} {stop_mmax} {stop_nmax} {stop_nth} {stop_nanim} {stop_nerr}\n"
        )
        f.write("/TFILE/0\n")
        f.write(f"{tfile_dt}\n")
        f.write("/VERS/2024\n")
        f.write("/DT/NODA/CST/0\n")
        f.write(f"{dt_ratio} 0 0\n")
        f.write("/ANIM/DT\n")
        f.write(f"0 {anim_dt}\n")
        if h3d_dt is not None:
            f.write("/H3D/DT\n")
            f.write(f"0 {h3d_dt}\n")
        if rfile_cycle is not None:
            if rfile_n is not None:
                f.write(f"/RFILE/{rfile_n}\n")
            else:
                f.write("/RFILE\n")
            f.write(f"{rfile_cycle}\n")
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
                    if ftype == "BIQUAD":
                        alpha = fail.get("ALPHA", 0.0)
                        beta = fail.get("BETA", 0.0)
                        m = fail.get("M", 0.0)
                        n_fail = fail.get("N", 0.0)
                        f.write(f"/FAIL/BIQUAD/{mid}\n")
                        f.write("#    \u03b1      \u03b2      m      n\n")
                        f.write(f"  {alpha}   {beta}   {m}   {n_fail}\n")
                    elif ftype:
                        f.write(f"/{ftype}/{mid}\n")
                        vals = [str(v) for v in fail.values() if v != ftype]
                        if vals:
                            f.write(" ".join(vals) + "\n")

        # 3. NODES (from include file)
        if include_inc:
            f.write(f"#include {mesh_inc}\n")


        # 4. BOUNDARY CONDITIONS

        if boundary_conditions:
            for idx, bc in enumerate(boundary_conditions, start=1):
                bc_type = str(bc.get("type", "BCS")).upper()
                name = bc.get("name", f"BC_{idx}")
                nodes_bc = bc.get("nodes", [])
                gid = 100 + idx

                if bc_type == "BCS":
                    tra = str(bc.get("tra", "000")).rjust(3, "0")
                    rot = str(bc.get("rot", "000")).rjust(3, "0")
                    f.write(f"/BCS/{idx}\n")
                    f.write(f"{name}\n")
                    f.write("#  Tra rot   skew_ID  grnod_ID\n")
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

                f.write(f"/GRNOD/NODE/{gid}\n")
                f.write(f"{name}_nodes\n")
                for nid in nodes_bc:
                    f.write(f"{nid:10d}\n")

        if interfaces:
            for idx, inter in enumerate(interfaces, start=1):
                itype = inter.get("type", "TYPE2").upper()
                s_nodes = inter.get("slave", [])
                m_nodes = inter.get("master", [])
                name = inter.get("name", f"INTER_{idx}")
                fric = inter.get("fric", 0.0)
                slave_id = 200 + idx
                master_id = 300 + idx

                if itype == "TYPE7":
                    gap = inter.get("gap", 0.0)
                    stif = inter.get("stiff", 0.0)
                    igap = inter.get("igap", 0)
                    f.write(f"/INTER/TYPE7/{idx}\n")
                    f.write(f"{name}\n")
                    f.write(f"{slave_id} {master_id} {stif} {gap} {igap}\n")
                    f.write("/FRICTION\n")
                    f.write(f"{fric}\n")
                else:
                    f.write(f"/INTER/TYPE2/{idx}\n")
                    f.write(f"{name}\n")
                    f.write(f"{slave_id} {master_id}\n")
                    f.write("/FRICTION\n")
                    f.write(f"{fric}\n")

                f.write(f"/GRNOD/NODE/{slave_id}\n")
                f.write(f"{name}_slave\n")
                for nid in s_nodes:
                    f.write(f"{nid:10d}\n")
                f.write(f"/GRNOD/NODE/{master_id}\n")
                f.write(f"{name}_master\n")
                for nid in m_nodes:
                    f.write(f"{nid:10d}\n")

        # 5. PARTS
        f.write(f"/PART/1/1/1\n")
        f.write(f"/PROP/SHELL/1 {thickness} 0\n")

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
            g = gravity.get("g", 9.81)
            nx = gravity.get("nx", 0.0)
            ny = gravity.get("ny", 0.0)
            nz = gravity.get("nz", -1.0)
            comp = int(gravity.get("comp", 3))
            f.write("/GRAVITY\n")
            f.write(f"{comp} {g}\n")
            f.write(f"{nx} {ny} {nz}\n")

        f.write("/END\n")


def write_minimal_rad(
    outfile: str,
    mesh_inc: str = "mesh.inc",
    runname: str = DEFAULT_RUNNAME,
    *,
    include_inc: bool = True,
) -> None:
    """Generate a minimal starter file referencing only the mesh.

    Set ``include_inc`` to ``False`` to omit the ``#include`` line.
    """

    with open(outfile, "w") as f:
        f.write("#RADIOSS STARTER\n")
        f.write("/BEGIN\n")
        f.write(f"{runname}\n")
        f.write("     2024         0\n")
        f.write("                  kg                  mm                   s\n")
        f.write("                  kg                  mm                   s\n")
        if include_inc:
            f.write(f"#include {mesh_inc}\n")
        f.write("/END\n")
