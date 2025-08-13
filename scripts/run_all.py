"""CLI to convert .cdb files and optionally run OpenRadioss.

Adds convenience flags to execute the Starter/Engine and set required
environment variables following the OpenRadioss installation layout.
"""
import argparse
import os
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
from cdb2rad.writer_inp import write_inp


def main() -> None:
    parser = argparse.ArgumentParser(description="Process .cdb file")
    parser.add_argument("cdb_file", help="Input .cdb file")
    parser.add_argument("--starter", dest="starter", help="Output starter file")
    parser.add_argument(
        "--rad",
        dest="starter",
        help="Deprecated alias for --starter",
    )
    parser.add_argument("--engine", dest="engine", help="Output engine file")
    parser.add_argument("--inc", dest="inc", help="Output mesh.inc file")
    parser.add_argument("--inp", dest="inp", help="Output Abaqus .inp file")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate starter, engine, inc and inp with default names",
    )
    # Execution and environment options
    parser.add_argument(
        "--exec",
        dest="exec_path",
        help="Run OpenRadioss starter after generation (deprecated, use --starter-exec)",
    )
    parser.add_argument(
        "--starter-exec",
        dest="starter_exec",
        help="Path to OpenRadioss starter binary (starter_linux64_gf)",
    )
    parser.add_argument(
        "--engine-exec",
        dest="engine_exec",
        help="Path to OpenRadioss engine binary (engine_linux64_gf)",
    )
    parser.add_argument(
        "--ld-library-path",
        dest="ld_library_path",
        help="LD_LIBRARY_PATH to use when running OpenRadioss",
    )
    parser.add_argument(
        "--rad-cfg-path",
        dest="rad_cfg_path",
        help="RAD_CFG_PATH to use when running OpenRadioss",
    )
    parser.add_argument(
        "--auto-env",
        action="store_true",
        help="Auto-detect LD_LIBRARY_PATH and RAD_CFG_PATH from openradioss_bin",
    )
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
    parser.add_argument(
        "--no-cdb-materials",
        action="store_true",
        help="Ignore material definitions extracted from the .cdb file",
    )
    parser.add_argument(
        "--anim-presets",
        action="store_true",
        help="Add common /ANIM stress/strain requests for shell and brick",
    )

    args = parser.parse_args()

    if args.all or not (args.starter or args.engine or args.inc or args.inp):
        args.inc = args.inc or "mesh.inc"
        args.starter = args.starter or "model_0000.rad"
        args.engine = args.engine or "model_0001.rad"
        args.inp = args.inp or "model.inp"

    nodes, elements, node_sets, elem_sets, materials = parse_cdb(args.cdb_file)

    if args.inc:
        write_mesh_inc(
            nodes,
            elements,
            args.inc,
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=None if args.no_cdb_materials else materials,
        )
    if args.inp:
        write_inp(
            nodes,
            elements,
            args.inp,
            node_sets=node_sets,
            elem_sets=elem_sets,
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
            materials=None if args.no_cdb_materials else materials,
            default_material=not args.no_default_material,
        )
    if args.engine:
        write_engine(
            args.engine,
            runname=Path(args.starter or "model").stem.replace("_0000", ""),
            anim_presets=args.anim_presets,
        )

    # Optional execution of Starter/Engine with environment setup
    starter_exec = args.starter_exec or args.exec_path
    engine_exec = args.engine_exec

    if starter_exec or engine_exec:
        env = os.environ.copy()

        # Auto-detect env vars from default OpenRadioss bundle
        if args.auto_env or (args.ld_library_path is None and args.rad_cfg_path is None):
            root = ROOT / 'openradioss_bin' / 'OpenRadioss'
            ld_guess = root / 'extlib' / 'hm_reader' / 'linux64'
            cfg_guess = root / 'hm_cfg_files'
            if args.ld_library_path is None and ld_guess.exists():
                env['LD_LIBRARY_PATH'] = str(ld_guess)
            if args.rad_cfg_path is None and cfg_guess.exists():
                env['RAD_CFG_PATH'] = str(cfg_guess)

        # Explicit overrides
        if args.ld_library_path:
            env['LD_LIBRARY_PATH'] = args.ld_library_path
        if args.rad_cfg_path:
            env['RAD_CFG_PATH'] = args.rad_cfg_path

        # Prepare inputs
        starter_in = args.starter
        engine_in = args.engine

        if starter_exec and starter_in:
            subprocess.run([str(starter_exec), '-i', str(starter_in)], env=env, check=False)

        if engine_exec and engine_in:
            subprocess.run([str(engine_exec), '-i', str(engine_in)], env=env, check=False)


if __name__ == "__main__":
    main()
