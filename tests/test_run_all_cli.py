from pathlib import Path
import subprocess

DATA = Path(__file__).resolve().parents[1] / 'data' / 'model.cdb'
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'run_all.py'


def test_rad_alias(tmp_path):
    starter = tmp_path / 'alias.rad'
    result = subprocess.run([
        'python', str(SCRIPT), str(DATA), '--rad', str(starter)
    ], capture_output=True, text=True, cwd=tmp_path)
    assert starter.exists()


def test_all_flag(tmp_path):
    result = subprocess.run([
        'python', str(SCRIPT), str(DATA), '--all'
    ], capture_output=True, text=True, cwd=tmp_path)
    assert (tmp_path / 'mesh.inc').exists()
    assert (tmp_path / 'model_0000.rad').exists()
    assert (tmp_path / 'model_0001.rad').exists()


def test_inp_flag(tmp_path):
    out = tmp_path / 'mesh.inp'
    result = subprocess.run([
        'python', str(SCRIPT), str(DATA), '--inp', str(out)
    ], capture_output=True, text=True, cwd=tmp_path)
    assert out.exists()

