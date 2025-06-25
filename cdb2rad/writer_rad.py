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

    write_mesh_inc(
        nodes,
        elements,
        mesh_inc,
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
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

        f.write("/PART/1\n")
        f.write("Part1\n")
        f.write("1 1 0\n")

        f.write("/PROP/SHELL/1\n")
        f.write(f"{thickness}\n")

        if not materials:
            f.write("/MAT/LAW1/1\n")
            f.write(f"{young} {poisson} {density}\n")
        else:
            for mid, props in materials.items():
                e = props.get("EX", young)
                nu = props.get("NUXY", poisson)
                rho = props.get("DENS", density)
                f.write(f"/MAT/LAW1/{mid}\n")
                f.write(f"{e} {nu} {rho}\n")

        f.write("/BCS/1\n")
        f.write("1 1 1 1 1 1\n")


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
