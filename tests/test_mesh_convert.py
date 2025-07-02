from cdb2rad.mesh_convert import convert_to_vtk
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data' / 'model.cdb'


def test_convert_to_vtk(tmp_path):
    out = tmp_path / 'mesh.vtk'
    convert_to_vtk(str(DATA), str(out))
    text = out.read_text()
    assert 'UNSTRUCTURED_GRID' in text
    assert 'POINT_DATA' in text



def test_convert_to_vtp(tmp_path):
    out = tmp_path / 'mesh.vtp'
    convert_to_vtk(str(DATA), str(out))
    txt = out.read_text()
    assert '<VTKFile' in txt or 'UNSTRUCTURED_GRID' in txt
    assert 'POINT_DATA' in txt or '<PointData>' in txt
