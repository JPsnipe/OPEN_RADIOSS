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

    validate_rad_format(str(starter))
    validate_rad_format(str(engine))
