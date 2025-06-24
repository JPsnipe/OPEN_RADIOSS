"""CLI to convert .cdb files."""
import argparse

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.writer_rad import write_rad


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--rad", dest="rad", help="Output .rad file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inc file")

    args = parser.parse_args()

    nodes, elements = parse_cdb(args.cdb_file)

    if args.inc:
        write_mesh_inc(nodes, elements, args.inc)
    if args.rad:
        write_rad(nodes, elements, args.rad)


if __name__ == "__main__":
    main()
