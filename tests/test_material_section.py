import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_starter

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_material_blocks(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    extra = {
        20: {
            'LAW': 'LAW36',
            'NAME': 'DP600',
            'CURVE': [(0.0, 300.0), (0.1, 400.0)],
        }
    }
    rad = tmp_path / 'mat_0000.rad'
    write_starter(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        extra_materials=extra,
    )
    lines = rad.read_text().splitlines()
    mat_count = sum(1 for l in lines if l.startswith('/MAT/'))
    assert mat_count == len(mats) + len(extra)
    idxs = [i for i, l in enumerate(lines) if l.startswith('/MAT/')]
    for idx in idxs:
        assert len(lines) > idx + 2
    if any('/MAT/LAW36/' in lines[i] for i in idxs):
        idx = next(i for i, l in enumerate(lines) if l.startswith('/MAT/LAW36/'))
        fct_line = next(l for l in lines[idx:] if l.startswith('# fct_IDp'))
        fct_id = int(lines[lines.index(fct_line) + 1].split()[0])
        assert any(line.startswith(f'/FUNCT/{fct_id}') for line in lines)


def test_material_id_offset(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    # Extra material using an ID already present in mats
    extra = {1: {'LAW': 'LAW1', 'EX': 1e5, 'NUXY': 0.3, 'DENS': 7800.0}}
    rad = tmp_path / 'offset_0000.rad'
    write_starter(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        extra_materials=extra,
    )
    text = rad.read_text()
    mat_lines = [l for l in text.splitlines() if l.startswith('/MAT/')]
    ids = [int(l.split('/')[3]) for l in mat_lines]
    assert len(ids) == len(mats) + 1
    assert len(ids) == len(set(ids))
