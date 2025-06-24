import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inp
from cdb2rad.writer_rad import write_rad

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_parse_cdb():
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    assert len(nodes) == 2032
    assert len(elements) == 2479
    assert "BALL" in elem_sets
    assert "TARGET" in elem_sets
    assert elem_sets["BALL"][0] == 1
    assert elem_sets["BALL"][-1] == 715
    assert elem_sets["TARGET"][0] == 918
    assert elem_sets["TARGET"][-1] == 2681


def test_write_mesh(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    out = tmp_path / 'mesh.inp'
    write_mesh_inp(
        nodes,
        elements,
        str(out),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
    )
    text = out.read_text()
    assert '/NODE' in text
    assert '/BRICK' in text


def test_write_rad(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    rad = tmp_path / 'model.rad'
    write_rad(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
    )
    content = rad.read_text()
    assert '/BEGIN' in content
    assert '/END' in content
