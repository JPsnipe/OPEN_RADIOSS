import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_starter

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
