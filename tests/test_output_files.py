import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.writer_rad import write_starter, write_engine
from cdb2rad.rad_validator import validate_rad_format

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_output_files(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    mesh = tmp_path / 'mesh.inc'
    starter = tmp_path / 'model_0000.rad'
    engine = tmp_path / 'model_0001.rad'

    write_mesh_inc(
        nodes,
        elements,
        str(mesh),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
    )

    write_starter(
        nodes,
        elements,
        str(starter),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
    )
    write_engine(str(engine))

    text = mesh.read_text()
    assert text.startswith('/NODE')
    assert ('/SHELL' in text) or ('/BRICK' in text)
    assert '/SHELL/2000001' in text or '/BRICK/2000001' in text

    rad_text = starter.read_text()
    assert '/PART/2000001' in rad_text

    validate_rad_format(str(starter))
    validate_rad_format(str(engine))


def test_output_files_fric_id(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    starter = tmp_path / 'fid_0000.rad'
    engine = tmp_path / 'fid_0001.rad'

    frictions = [{
        'id': 1,
        'title': 'test no 1',
        'fric': 0.2,
    }]

    interfaces = [{
        'type': 'TYPE2',
        'name': 'cnt',
        'slave': [1, 2],
        'master': [3, 4],
        'fric_ID': 1,
    }]

    write_starter(nodes, elements, str(starter), interfaces=interfaces, frictions=frictions)
    write_engine(str(engine))

    txt = starter.read_text()
    assert '/FRICTION/1' in txt
    assert '/INTER/TYPE2/1' in txt

    validate_rad_format(str(starter))
    validate_rad_format(str(engine))
