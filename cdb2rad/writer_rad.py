"""Create a basic Radioss starter file."""

from typing import Dict, List, Tuple

from .writer_inc import write_mesh_inp


def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    outfile: str,
    mesh_inc: str = "mesh.inp",
) -> None:
    """Generate a minimal ``model_0000.rad`` file and the referenced mesh."""

    write_mesh_inp(nodes, elements, mesh_inc)

    with open(outfile, 'w') as f:
        f.write("/BEGIN\n")
        f.write(f"/INCLUDE \"{mesh_inc}\"\n")
        f.write("/PART/1/1/1\n")
        f.write("/PROP/1\n")
        f.write("/MAT/1\n")
        f.write("/END\n")
