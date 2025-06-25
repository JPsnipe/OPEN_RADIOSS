#!/usr/bin/env python3
"""Prepare virtual environment and download OpenRadioss for testing."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    create = ROOT / 'scripts' / 'create_venv.py'
    download = ROOT / 'scripts' / 'download_openradioss.py'

    # create virtual environment if needed
    if not (ROOT / '.venv').exists():
        subprocess.run([sys.executable, str(create)], check=True)
    else:
        print('Virtual environment already exists')

    # download OpenRadioss binaries
    subprocess.run([sys.executable, str(download)], check=True)

    ld = ROOT / 'openradioss_bin' / 'OpenRadioss' / 'extlib' / 'hm_reader' / 'linux64'
    cfg = ROOT / 'openradioss_bin' / 'OpenRadioss' / 'hm_cfg_files'

    print('\nSet the following variables before running the starter:')
    print(f'export LD_LIBRARY_PATH={ld}')
    print(f'export RAD_CFG_PATH={cfg}')
    print('\nThen run `pytest -q` to execute the tests.')


if __name__ == '__main__':
    main()
