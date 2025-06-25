"""CLI to convert .cdb files."""
import argparse
import subprocess
import sys
from pathlib import Path

# Ensure the repository root is on sys.path when executed directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.writer_rad import write_rad
from cdb2rad.utils import extract_material_block


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--rad", dest="rad", help="Output .rad file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inc file")
    parser.add_argument("--exec", dest="exec_path", help="Run OpenRadioss starter after generation")
    parser.add_argument("--mat-file", dest="mat_file", help="Optional material block from .rad file")

    args = parser.parse_args()

    if not args.rad and not args.inc:
        # default output names when none are provided
        args.inc = "mesh.inc"
        args.rad = "model_0000.rad"

    nodes, elements, node_sets, elem_sets, materials = parse_cdb(args.cdb_file)

    if args.inc:
        write_mesh_inc(
            nodes,
            elements,
            args.inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=materials,
        )
    if args.rad:
        write_rad(
            nodes,
            elements,
            args.rad,
            mesh_inc=args.inc or "mesh.inc",
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=materials if not args.mat_file else None,
            material_lines=(extract_material_block(args.mat_file) if args.mat_file else None),
            mat_id=2 if args.mat_file else 1,
        )
        if args.exec_path:
            subprocess.run([args.exec_path, '-i', args.rad], check=False)


if __name__ == "__main__":
    main()
