"""Create a basic Radioss .rad file."""
from typing import Dict, List, Tuple

from .writer_inc import write_mesh_inc


def write_rad(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, str, List[int]]],
    outfile: str,
    mesh_inc: str = 'mesh.inc',
) -> None:
    """Generate a minimal model_0000.rad file."""
    write_mesh_inc(nodes, elements, mesh_inc)

    with open(outfile, 'w') as f:
        f.write('/BEGIN\n')
        f.write(f'/INCLUDE "{mesh_inc}"\n')
        f.write('/PART\n1, 1, 1\n')
        f.write('/PROP\n1, SHELL\n')
        f.write('/MAT\n1, STEEL\n')
        f.write('/END\n')
