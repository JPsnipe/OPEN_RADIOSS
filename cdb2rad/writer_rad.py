"""Create a basic Radioss starter file.

The block syntax follows the Radioss Input Reference Guide. Sections such
as ``/BCS`` for boundary conditions, ``/INTER`` for contact definitions and
``/IMPVEL`` for initial velocities are optional and can be enabled via
function parameters.
"""

from typing import Dict, List, Tuple

from .writer_inc import write_mesh_inc

DEFAULT_THICKNESS = 1.0
DEFAULT_E = 210000.0
DEFAULT_NU = 0.3
DEFAULT_RHO = 7800.0
DEFAULT_FINAL_TIME = 0.01
DEFAULT_ANIM_DT = 0.001
DEFAULT_HISTORY_DT = 1e-5
DEFAULT_DT_RATIO = 0.9
DEFAULT_RUNNAME = "model"


def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mesh_inc: str = "mesh.inc",
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
    boundary_conditions: List[Dict[str, object]] | None = None,
    interfaces: List[Dict[str, object]] | None = None,
    init_velocity: Dict[str, object] | None = None,
    gravity: Dict[str, float] | None = None,

) -> None:
    """Generate ``model_0000.rad`` with optional solver controls.

    Parameters allow customizing material properties and basic engine
    settings such as final time, animation frequency and time-step
    controls. Gravity loading can be specified via the ``gravity``
    parameter.
    """

    all_mats: Dict[int, Dict[str, float]] = {}
    if materials:
        all_mats.update(materials)
    if extra_materials:
        all_mats.update(extra_materials)

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
        f.write(f"/RUN/{runname}/1/\n")
        f.write(f"                {t_end}\n")
        f.write("/STOP\n")
        f.write("0 0 0 1 1 0\n")
        f.write("/TFILE/0\n")
        f.write(f"{tfile_dt}\n")
        f.write("/VERS/2024\n")
        f.write("/DT/NODA/CST/0\n")
        f.write(f"{dt_ratio} 0 0\n")
        f.write("/ANIM/DT\n")
        f.write(f"0 {anim_dt}\n")

        # 2. MATERIALS
        if not all_mats:
            f.write("/MAT/LAW1/1\n")
            f.write("Default_Mat\n")
            f.write("#              RHO\n")
            f.write(f"{density}\n")
            f.write("#                  E                  Nu\n")
            f.write(f"{young} {poisson}\n")
        else:
            for mid, props in all_mats.items():
                law = props.get("LAW", "LAW1").upper()
                e = props.get("EX", young)
                nu = props.get("NUXY", poisson)
                rho = props.get("DENS", density)
                if law in ("LAW2", "JOHNSON_COOK"):
                    a = props.get("A", 0.0)
                    b = props.get("B", 0.0)
                    n = props.get("N", 0.0)
                    c = props.get("C", 0.0)
                    eps0 = props.get("EPS0", 1.0)
                    f.write(f"/MAT/LAW2/{mid}\n")
                    f.write(f"{rho} {e} {nu}\n")
                    f.write(f"{a} {b} {n} {c} {eps0}\n")
                else:
                    name = props.get("NAME", f"MAT_{mid}")
                    f.write(f"/MAT/LAW1/{mid}\n")
                    f.write(f"{name}\n")
                    f.write("#              RHO\n")
                    f.write(f"{rho}\n")
                    f.write("#                  E                  Nu\n")
                    f.write(f"{e} {nu}\n")

        # 3. NODES (from include file)
        f.write(f"#include {mesh_inc}\n")


        # Basic engine control cards
        f.write("/STOP\n")
        f.write(f"{t_end}\n")
        f.write("0 0 0 1 1 0\n")
        f.write("/TFILE/0\n")
        f.write(f"{tfile_dt}\n")
        f.write("/VERS/2024\n")
        f.write("/DT/NODA/CST/0\n")
        f.write(f"{dt_ratio} 0 0\n")
        f.write("/ANIM/DT\n")
        f.write(f"0 {anim_dt}\n")


        # 4. BOUNDARY CONDITIONS

        if boundary_conditions:
            for idx, bc in enumerate(boundary_conditions, start=1):
                name = bc.get("name", f"BC_{idx}")
                tra = str(bc.get("tra", "000")).rjust(3, "0")
                rot = str(bc.get("rot", "000")).rjust(3, "0")
                nodes_bc = bc.get("nodes", [])
                gid = 100 + idx
                f.write(f"/BCS/{idx}\n")
                f.write(f"{name}\n")
                f.write("#  Tra rot   skew_ID  grnod_ID\n")
                f.write(f"   {tra} {rot}         0        {gid}\n")
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
) -> None:
    """Generate a minimal starter file referencing only the mesh."""

    with open(outfile, "w") as f:
        f.write("#RADIOSS STARTER\n")
        f.write("/BEGIN\n")
        f.write(f"{runname}\n")
        f.write("     2024         0\n")
        f.write("                  kg                  mm                   s\n")
        f.write("                  kg                  mm                   s\n")
        f.write(f"#include {mesh_inc}\n")
        f.write("/END\n")
