#!/usr/bin/env python3
"""Convert a mesh file to VTK format."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cdb2rad.mesh_convert import convert_to_vtk


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert mesh to VTK")
    parser.add_argument("input", help="Input mesh file (.cdb/.inp/.rad/.inc)")
    parser.add_argument("output", help="Output VTK file")
    args = parser.parse_args()
    convert_to_vtk(args.input, args.output)
    print(f"Written {args.output}")


if __name__ == "__main__":
    main()
