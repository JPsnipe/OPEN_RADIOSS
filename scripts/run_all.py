"""CLI to convert .cdb files."""
import argparse
import subprocess

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inp
from cdb2rad.writer_rad import write_rad


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--rad", dest="rad", help="Output .rad file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inp file")
    parser.add_argument(
        "--exec",
        dest="exec_path",
        help="Run OpenRadioss starter after generation",
    )

    args = parser.parse_args()

    nodes, elements = parse_cdb(args.cdb_file)

    if args.inc:
        write_mesh_inp(nodes, elements, args.inc)
    if args.rad:
        write_rad(nodes, elements, args.rad)
        if args.exec_path:
            from pathlib import Path
            import os

            exe = Path(args.exec_path).resolve()
            base = exe.parent.parent
            env = os.environ.copy()
            env.setdefault('RAD_CFG_PATH', str(base / 'hm_cfg_files'))
            env.setdefault('LD_LIBRARY_PATH', str(base / 'extlib' / 'hm_reader' / 'linux64'))
            subprocess.run([str(exe), '-i', args.rad], check=False, env=env)


if __name__ == "__main__":
    main()
