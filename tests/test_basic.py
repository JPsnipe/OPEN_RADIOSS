import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inp
from cdb2rad.writer_rad import write_rad
from cdb2rad.utils import element_summary

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


def test_element_summary():
    _, elements, _, _, _ = parse_cdb(DATA)
    etype_counts, kw_counts = element_summary(elements)
    assert sum(kw_counts.values()) == len(elements)
    assert kw_counts["BRICK"] > 0


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
        thickness=2.0,
        young=1e5,
        poisson=0.25,
        density=7000.0,

        runname="demo",
        t_end=0.02,
        anim_dt=0.002,
        tfile_dt=0.0001,
        dt_ratio=0.8,

    )
    content = rad.read_text()
    assert '/BEGIN' in content
    assert '/END' in content
    assert '2.0' in content
    assert '100000.0' in content

    assert '/RUN/demo/1/' in content
    assert '0.02' in content
    assert '0.002' in content
    assert '0.0001' in content


def test_write_mesh_without_sets_materials(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    out = tmp_path / 'mesh_no_sets.inp'
    write_mesh_inp(nodes, elements, str(out))
    content = out.read_text()
    assert '/GRNOD' not in content
    assert '/SET/EL' not in content
    assert '/MAT/LAW1' not in content

