"""Create a basic Radioss starter file."""

from typing import Dict, List, Tuple

from .writer_inc import write_mesh_inp

DEFAULT_THICKNESS = 1.0
DEFAULT_E = 210000.0
DEFAULT_NU = 0.3
DEFAULT_RHO = 7800.0


def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mesh_inc: str = "mesh.inp",
    node_sets: Dict[str, List[int]] | None = None,
    elem_sets: Dict[str, List[int]] | None = None,
    materials: Dict[int, Dict[str, float]] | None = None,
) -> None:
    """Generate a minimal ``model_0000.rad`` file and the referenced mesh."""

    write_mesh_inp(
        nodes,
        elements,
        mesh_inc,
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
    )

    with open(outfile, "w") as f:
        f.write("/BEGIN\n")
        f.write(f"/INCLUDE \"{mesh_inc}\"\n")

        f.write("/PART/1\n")
        f.write("/PART/1/1/1\n")

        f.write("/PROP/SHELL/1\n")
        f.write(f"{DEFAULT_THICKNESS}\n")

        if not materials:
            f.write("/MAT/LAW1/1\n")
            f.write(f"{DEFAULT_E} {DEFAULT_NU} {DEFAULT_RHO}\n")
        else:
            for mid, props in materials.items():
                e = props.get("EX", DEFAULT_E)
                nu = props.get("NUXY", DEFAULT_NU)
                rho = props.get("DENS", DEFAULT_RHO)
                f.write(f"/MAT/LAW1/{mid}\n")
                f.write(f"{e} {nu} {rho}\n")

        f.write("/BOUNDARY/BCS/1\n")
        f.write("1 1 1 1 1 1\n")

        f.write("/LOAD/PBLAST/1\n")
        f.write("0.0 0.0 0.0\n")

        f.write("/INTER/TYPE7/1\n")
        f.write("0 0 0.0 0.0 0.0\n")

        f.write("/SENSOR/SPRING/1\n")
        f.write("0.0\n")

        f.write("/END\n")
