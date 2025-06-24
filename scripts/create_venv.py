#!/usr/bin/env python3
"""Create a local virtual environment and install dev tools."""
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path('.venv')


def main() -> None:
    if VENV_DIR.exists():
        print(f"Virtual environment already exists at {VENV_DIR}")
        return
    subprocess.run([sys.executable, '-m', 'venv', str(VENV_DIR)], check=True)
    pip = VENV_DIR / 'bin' / 'pip'
    if not pip.exists():
        pip = VENV_DIR / 'Scripts' / 'pip.exe'
    packages = ['pytest']
    subprocess.run([str(pip), 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([str(pip), 'install', *packages], check=True)
    print('Virtual environment ready')


if __name__ == '__main__':
    main()
