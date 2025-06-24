import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inp
from cdb2rad.writer_rad import write_rad

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_parse_cdb():
    nodes, elements = parse_cdb(DATA)
    assert len(nodes) == 8
    assert len(elements) == 2


def test_write_mesh(tmp_path):
    nodes, elements = parse_cdb(DATA)
    out = tmp_path / 'mesh.inp'
    write_mesh_inp(nodes, elements, str(out))
    text = out.read_text()
    assert '/NODE' in text
    assert '/SHELL' in text
    assert '/BRICK' in text


def test_write_rad(tmp_path):
    nodes, elements = parse_cdb(DATA)
    rad = tmp_path / 'model.rad'
    write_rad(nodes, elements, str(rad))
    content = rad.read_text()
    assert '/BEGIN' in content
    assert '/END' in content
