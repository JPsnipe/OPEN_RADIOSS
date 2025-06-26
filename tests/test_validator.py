import os
import pytest
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad
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
    rad = tmp_path / 'model.rad'
    write_rad(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        boundary_conditions=[{'name': 'f', 'tra': '111', 'rot': '000', 'nodes': [1]}],
        interfaces=[{'type': 'TYPE7', 'name': 'c', 'slave': [1], 'master': [2]}],
        init_velocity={'nodes': [1], 'vx': 1.0},
        gravity={'g': 9.81, 'nz': -1.0},
    )
    validate_rad_format(str(rad))


def test_invalid_keyword(tmp_path):
    bad = tmp_path / "bad.rad"
    bad.write_text("/UNKNOWN\n1 2 3\n")
    with pytest.raises(ValueError):
        validate_rad_format(str(bad))


def test_validate_subset(tmp_path):
    rad = tmp_path / "subset.rad"
    rad.write_text("/SUBSET/1\nset1\n1 2 3\n/END\n")
    validate_rad_format(str(rad))
