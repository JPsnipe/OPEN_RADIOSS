from cdb2rad.parser import parse_cdb
from cdb2rad.vtk_writer import write_vtk
import os
import tempfile

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_write_vtk():
    nodes, elements, *_ = parse_cdb(DATA)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.vtk') as tmp:
        write_vtk(nodes, elements, tmp.name)
        tmp.close()
        with open(tmp.name, 'r') as f:
            content = f.read()
    assert content.startswith('# vtk DataFile')
    assert 'DATASET UNSTRUCTURED_GRID' in content
