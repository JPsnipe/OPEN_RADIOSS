#!/usr/bin/env python3
"""Launch ParaView Web Visualizer for a .cdb mesh."""
import argparse
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start ParaView Web server")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument(
        "--port",
        type=int,
        default=12345,
        help="Port for the web server",
    )
    args = parser.parse_args()

    from cdb2rad.parser import parse_cdb
    from cdb2rad.vtk_writer import write_vtk

    nodes, elements, *_ = parse_cdb(args.cdb_file)

    tmp_dir = tempfile.mkdtemp()
    vtk_path = Path(tmp_dir) / "mesh.vtk"
    write_vtk(nodes, elements, str(vtk_path))

    cmd = [
        "pvpython",
        "-m",
        "paraview.apps.visualizer",
        "--data",
        str(vtk_path),
        "--port",
        str(args.port),
    ]

    print(
        "Starting ParaView Web Visualizer at "
        f"http://localhost:{args.port}/ (Ctrl+C to stop)"
    )
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
