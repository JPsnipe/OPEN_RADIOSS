#!/usr/bin/env python3
"""Download and extract the latest OpenRadioss binary release."""
from __future__ import annotations
import json
import urllib.request
import zipfile
from pathlib import Path
import sys
import os
import tempfile

DEST = Path('openradioss_bin')
API_URL = 'https://api.github.com/repos/OpenRadioss/OpenRadioss/releases/latest'


def latest_linux_asset() -> str | None:
    with urllib.request.urlopen(API_URL) as resp:
        release = json.load(resp)
    for asset in release.get('assets', []):
        name = asset.get('name', '')
        if name.endswith('linux64.zip'):
            return asset['browser_download_url']
    return None


def download(url: str, path: Path) -> None:
    with urllib.request.urlopen(url) as resp, open(path, 'wb') as out:
        out.write(resp.read())


def main() -> None:
    exec_dir = DEST / 'OpenRadioss' / 'exec'
    if exec_dir.exists():
        print('OpenRadioss already installed')
        return
    asset_url = latest_linux_asset()
    if not asset_url:
        print('Could not find OpenRadioss asset', file=sys.stderr)
        sys.exit(1)
    DEST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / 'or.zip'
        print(f'Downloading {asset_url}...')
        download(asset_url, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(DEST)

    for exe in (
        'starter_linux64_gf',
        'starter_linux64_gf_sp',
        'engine_linux64_gf',
        'engine_linux64_gf_sp',
    ):
        path = exec_dir / exe
        if path.exists():
            os.chmod(path, os.stat(path).st_mode | 0o111)

    print(f'OpenRadioss extracted to {DEST}')


if __name__ == '__main__':
    main()
