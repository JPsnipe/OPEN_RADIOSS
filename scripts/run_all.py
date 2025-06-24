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
from cdb2rad.writer_inc import write_mesh_inp
from cdb2rad.writer_rad import write_rad


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--rad", dest="rad", help="Output .rad file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inp file")
    parser.add_argument("--exec", dest="exec_path", help="Run OpenRadioss starter after generation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show summary information during execution")

    args = parser.parse_args()

    if not args.rad and not args.inc:
        # default output names when none are provided
        args.inc = "mesh.inp"
        args.rad = "model_0000.rad"

    nodes, elements, node_sets, elem_sets, materials = parse_cdb(args.cdb_file)

    if args.verbose:
        print(
            f"Parsed {len(nodes)} nodes, {len(elements)} elements from '{args.cdb_file}'. "
            f"{len(node_sets)} node sets, {len(elem_sets)} element sets, {len(materials)} materials."
        )

    if args.inc:
        write_mesh_inp(
            nodes,
            elements,
            args.inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=materials,
        )
        if args.verbose:
            print(f"Mesh include written to '{args.inc}'")
    if args.rad:
        write_rad(
            nodes,
            elements,
            args.rad,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=materials,
        )
        if args.verbose:
            print(f"Starter file written to '{args.rad}'")
        if args.exec_path:
            subprocess.run([args.exec_path, '-i', args.rad], check=False)

    if args.verbose:
        print("Translation completed successfully")


if __name__ == "__main__":
    main()
