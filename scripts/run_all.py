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
from cdb2rad.writer_rad import write_starter, write_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--starter", dest="starter", help="Output starter file")
    parser.add_argument("--engine", dest="engine", help="Output engine file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inc file")
    parser.add_argument("--exec", dest="exec_path", help="Run OpenRadioss starter after generation")
    parser.add_argument(
        "--skip-include",
        action="store_true",
        help="Do not include the mesh.inc file inside the generated .rad",
    )
    parser.add_argument(
        "--no-run-cards",
        action="store_true",
        help="Omit /RUN and related control cards from the .rad file",
    )
    parser.add_argument(
        "--no-default-material",
        action="store_true",
        help="Do not insert a default material when none are provided",
    )

    args = parser.parse_args()

    if not args.starter and not args.engine and not args.inc:
        args.inc = "mesh.inc"
        args.starter = "model_0000.rad"
        args.engine = "model_0001.rad"

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
    if args.starter:
        write_starter(
            nodes,
            elements,
            args.starter,
            mesh_inc=args.inc or "mesh.inc",
            include_inc=not args.skip_include,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=materials,
            default_material=not args.no_default_material,
        )
    if args.engine:
        write_engine(
            args.engine,
            runname=Path(args.starter or "model").stem.replace("_0000", ""),
        )
        if args.exec_path and args.starter:
            subprocess.run([args.exec_path, '-i', args.starter], check=False)


if __name__ == "__main__":
    main()
