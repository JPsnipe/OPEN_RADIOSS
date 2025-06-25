"""Create a basic Radioss starter file."""

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

) -> None:
    """Generate ``model_0000.rad`` with optional solver controls.

    Parameters allow customizing material properties and basic engine
    settings such as final time, animation frequency and time-step
    controls.
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
        # radioss 2024 uses `#include` for file references
        f.write(f"#include {mesh_inc}\n")

        f.write(f"/PART/1/1/1\n")
        f.write(f"/PROP/SHELL/1 {thickness} 0\n")

        if not all_mats:
            f.write(f"/MAT/LAW1/1 {young} {poisson} {density}\n")
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
                    f.write(f"/MAT/LAW1/{mid} {e} {nu} {rho}\n")


        # Basic engine control cards
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

        f.write("/END\n")
