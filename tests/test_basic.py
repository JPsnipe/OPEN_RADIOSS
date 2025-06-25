import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.writer_rad import write_rad, write_minimal_rad
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
    out = tmp_path / 'mesh.inc'
    write_mesh_inc(
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
    assert content.startswith('#RADIOSS STARTER')
    assert '/BEGIN' in content
    assert '/END' in content
    assert '2.0' in content
    assert '100000.0' in content

    assert '/STOP' in content
    assert '0.02' in content
    assert '0.002' in content
    assert '0.0001' in content


def test_write_rad_extra_materials(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    extra = {
        99: {
            'LAW': 'LAW2',
            'EX': 1e5,
            'NUXY': 0.3,
            'DENS': 7800.0,
            'A': 200.0,
            'B': 400.0,
            'N': 0.5,
            'C': 0.01,
            'EPS0': 1.0,
        }
    }
    rad = tmp_path / 'model_extra.rad'
    write_rad(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
        extra_materials=extra,
    )
    txt = rad.read_text()
    assert '/MAT/LAW2/99' in txt


def test_write_mesh_without_sets_materials(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    out = tmp_path / 'mesh_no_sets.inc'
    write_mesh_inc(nodes, elements, str(out))
    content = out.read_text()
    assert '/GRNOD' not in content
    assert '/SET/EL' not in content
    assert '/MAT/LAW1' not in content


def test_write_minimal_rad(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'min.rad'
    write_minimal_rad(str(rad), mesh_inc='mesh.inc', runname='min')
    text = rad.read_text()
    assert text.startswith('#RADIOSS STARTER')
    assert '/BEGIN' in text
    assert '#include mesh.inc' in text
    assert '/END' in text


def test_write_rad_with_bc(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'bc.rad'
    bc = [{
        'name': 'fixed',
        'tra': '111',
        'rot': '111',
        'nodes': [1, 2]
    }]
    write_rad(nodes, elements, str(rad), boundary_conditions=bc)
    txt = rad.read_text()
    assert '/BCS/1' in txt
    assert 'fixed' in txt


def test_write_rad_with_impvel(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'vel.rad'
    write_rad(nodes, elements, str(rad), init_velocity={'nodes': [1], 'vx': 10.0})
    txt = rad.read_text()
    assert '/IMPVEL/1' in txt


def test_write_rad_with_gravity(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'grav.rad'
    write_rad(nodes, elements, str(rad), gravity={'g': 9.81, 'nz': -1.0})
    txt = rad.read_text()
    assert '/GRAVITY' in txt


def test_write_rad_with_type7_contact(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'contact7.rad'
    inter = [{
        'type': 'TYPE7',
        'name': 'cnt7',
        'slave': [1, 2],
        'master': [3, 4],
        'fric': 0.2,
    }]
    write_rad(nodes, elements, str(rad), interfaces=inter)
    txt = rad.read_text()
    assert '/INTER/TYPE7/1' in txt
    assert '/FRICTION' in txt


def test_write_rad_with_type2_contact(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'contact2.rad'
    inter = [{
        'type': 'TYPE2',
        'name': 'cnt2',
        'slave': [1, 2],
        'master': [3, 4],
        'fric': 0.1,
    }]
    write_rad(nodes, elements, str(rad), interfaces=inter)
    txt = rad.read_text()
    assert '/INTER/TYPE2/1' in txt
    assert '/FRICTION' in txt

