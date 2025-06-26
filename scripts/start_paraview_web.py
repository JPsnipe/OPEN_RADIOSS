#!/usr/bin/env python3
"""Launch ParaView Web Visualizer for a .cdb mesh."""
import argparse
import subprocess
import tempfile
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from cdb2rad.mesh_convert import convert_to_vtk


def main() -> None:
    parser = argparse.ArgumentParser(description="Start ParaView Web server")
    parser.add_argument("mesh_file", help="Input mesh (.cdb/.inp/.rad/.inc)")
    parser.add_argument(
        "--port",
        type=int,
        default=12345,
        help="Port for the web server",
    )
    args = parser.parse_args()

    tmp_dir = tempfile.mkdtemp()
    vtk_path = Path(tmp_dir) / "mesh.vtk"
    convert_to_vtk(args.mesh_file, str(vtk_path))

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
        f"Starting ParaView Web Visualizer at http://localhost:{args.port}/ (Ctrl+C to stop)"
    )
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
