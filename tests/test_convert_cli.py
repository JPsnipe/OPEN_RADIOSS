from pathlib import Path
import subprocess

DATA = Path(__file__).resolve().parents[1] / 'data' / 'model.cdb'


def test_convert_cli(tmp_path):
    out = tmp_path / 'mesh.vtk'
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'convert_to_vtk.py'
    result = subprocess.run(['python', str(script), str(DATA), str(out)], capture_output=True, text=True)
    assert out.exists()
    assert 'Written' in result.stdout
    text = out.read_text()
    assert 'POINT_DATA' in text



def test_convert_cli_vtp(tmp_path):

    out = tmp_path / 'mesh.vtp'
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'convert_to_vtk.py'
    result = subprocess.run(['python', str(script), str(DATA), str(out)], capture_output=True, text=True)
    assert out.exists()
    assert 'Written' in result.stdout
    text = out.read_text()
    assert 'POINT_DATA' in text or '<PointData>' in text

