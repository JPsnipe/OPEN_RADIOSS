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


def test_two_parts_two_subsets(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [
        {'id': 1, 'name': 'p1', 'pid': 1, 'mid': 1, 'set': 1},
        {'id': 2, 'name': 'p2', 'pid': 1, 'mid': 1, 'set': 2},
    ]
    subsets = {
        1: [elements[0][0]],
        2: [elements[1][0]],
    }
    rad = tmp_path / 'multi_subset.rad'
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
    idx1 = lines.index('/PART/1')
    idx2 = lines.index('/PART/2')
    subset_id1 = int(lines[idx1 + 2].split()[-1])
    subset_id2 = int(lines[idx2 + 2].split()[-1])
    assert subset_id1 == 1
    assert subset_id2 == 2


def test_two_parts_two_subsets_write_rad(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [
        {'id': 1, 'name': 'p1', 'pid': 1, 'mid': 1, 'set': 1},
        {'id': 2, 'name': 'p2', 'pid': 1, 'mid': 1, 'set': 2},
    ]
    subsets = {
        1: [elements[0][0]],
        2: [elements[1][0]],
    }
    rad = tmp_path / 'multi_subset_full.rad'
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
    idx1 = lines.index('/PART/1')
    idx2 = lines.index('/PART/2')
    subset_id1 = int(lines[idx1 + 2].split()[-1])
    subset_id2 = int(lines[idx2 + 2].split()[-1])
    assert subset_id1 == 1
    assert subset_id2 == 2


def test_subset_id_preserved(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    props = [{'id': 1, 'name': 'shell_p', 'type': 'SHELL', 'thickness': 1.0}]
    parts = [{'id': 1, 'name': 'p1', 'pid': 1, 'mid': 1, 'set': 5}]
    subsets = {5: [elements[0][0]]}
    rad = tmp_path / 'subset5_0000.rad'
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
    assert subset_id == 5
    assert '/SUBSET/5' in lines

