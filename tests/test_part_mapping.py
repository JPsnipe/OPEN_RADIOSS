import os
import pytest
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_starter, write_rad

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_part_material_mapping(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'part1', 'pid': 1, 'mid': 1}]
    extra = {1: {'LAW': 'LAW1', 'EX': 1e5, 'NUXY': 0.3, 'DENS': 7800.0}}
    rad = tmp_path / 'mapped_0000.rad'
    write_starter(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        extra_materials=extra,
        properties=props,
        parts=parts,
    )
    lines = rad.read_text().splitlines()
    idx = lines.index('/PART/1')
    mat_id = int(lines[idx + 2].split()[1])
    assert mat_id != 1
    assert any(line.startswith(f'/MAT/LAW1/{mat_id}') for line in lines)


def test_invalid_part_material(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'part1', 'pid': 1, 'mid': 999}]
    rad = tmp_path / 'invalid_0000.rad'
    with pytest.raises(ValueError):
        write_starter(
            nodes,
            elements,
            str(rad),
            node_sets=node_sets,
            elem_sets=elem_sets,
            materials=mats,
            properties=props,
            parts=parts,
        )


def test_part_subset_numeric(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'p1', 'pid': 1, 'mid': 1, 'set': 1}]
    subsets = {1: [elements[0][0]]}
    rad = tmp_path / 'subset_0000.rad'
    write_starter(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        properties=props,
        parts=parts,
        subsets=subsets,
        auto_subsets=False,
    )
    lines = rad.read_text().splitlines()
    idx = lines.index('/PART/1')
    subset_id = int(lines[idx + 2].split()[-1])
    assert subset_id == 1


def test_write_rad_part_subset(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'p1', 'pid': 1, 'mid': 1, 'set': 1}]
    subsets = {1: [elements[0][0]]}
    rad = tmp_path / 'subset_full.rad'
    write_rad(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        properties=props,
        parts=parts,
        subsets=subsets,
        auto_subsets=False,
    )
    lines = rad.read_text().splitlines()
    idx = lines.index('/PART/1')
    subset_id = int(lines[idx + 2].split()[-1])
    assert subset_id == 1


def test_return_subset_map(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'p', 'pid': 1, 'mid': 1, 'set': 'BALL'}]
    subsets = {'BALL': [elements[0][0]]}
    _, subset_map = write_starter(
        nodes,
        elements,
        str(tmp_path / 'ret_0000.rad'),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        properties=props,
        parts=parts,
        subsets=subsets,
        auto_subsets=False,
        return_subset_map=True,
    )
    assert subset_map == {'BALL': 1}

    _, subset_map = write_rad(
        nodes,
        elements,
        str(tmp_path / 'ret_full.rad'),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        properties=props,
        parts=parts,
        subsets=subsets,
        auto_subsets=False,
        return_subset_map=True,
    )
    assert subset_map == {'BALL': 1}
