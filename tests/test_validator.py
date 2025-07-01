import os
import pytest
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_starter, write_engine
from cdb2rad.rad_validator import validate_rad_format

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')
EXAMPLES = [
    os.path.join(os.path.dirname(__file__), '..', 'data_files', name)
    for name in (
        'gmsh_tensile_LAW36_BIQUAD_0000.rad',
        'gmsh_tensile_LAW36_BIQUAD_0001.rad',
        'Tube_Impact_0001.rad',
    )
]


@pytest.mark.parametrize('example', EXAMPLES)
def test_validate_examples(example):
    validate_rad_format(example)


def test_generated_rad_format(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    starter = tmp_path / 'model_0000.rad'
    engine = tmp_path / 'model_0001.rad'
    write_starter(
        nodes,
        elements,
        str(starter),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        boundary_conditions=[{'name': 'f', 'tra': '111', 'rot': '000', 'nodes': [1]}],
        interfaces=[{'type': 'TYPE7', 'name': 'c', 'slave': [1], 'master': [2]}],
        init_velocity={'nodes': [1], 'vx': 1.0},
        gravity={'g': 9.81, 'nz': -1.0},
    )
    write_engine(str(engine))
    validate_rad_format(str(starter))
    validate_rad_format(str(engine))


def test_invalid_keyword(tmp_path):
    bad = tmp_path / "bad.rad"
    bad.write_text("/UNKNOWN\n1 2 3\n")
    with pytest.raises(ValueError):
        validate_rad_format(str(bad))


def test_validate_subset(tmp_path):
    rad = tmp_path / "subset.rad"
    rad.write_text("/SUBSET/1\nset1\n1 2 3\n/END\n")
    validate_rad_format(str(rad))


def test_invalid_friction_simple(tmp_path):
    rad = tmp_path / "bad_fric.rad"
    rad.write_text("/FRICTION\n1 2 3\n")
    with pytest.raises(ValueError):
        validate_rad_format(str(rad))


def test_invalid_friction_multi(tmp_path):
    rad = tmp_path / "bad_fric_multi.rad"
    rad.write_text(
        "/FRICTION\ntitle\n0 0 0 2\n0 0 0 0 0\n0 0\n"
    )
    with pytest.raises(ValueError):
        validate_rad_format(str(rad))
